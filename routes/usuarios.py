from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cargo, User
from routes.decorators import cargos_permitidos


usuarios_bp = Blueprint("usuarios", __name__)


def _admins_ativos():
    return db.session.scalar(
        db.select(db.func.count(User.id)).where(
            User.cargo == Cargo.ADMINISTRADOR,
            User.ativo.is_(True),
        )
    ) or 0


def _ler_campos(form, usuario=None, incluir_senha=False):
    nome = form.get("nome", "").strip()
    email = form.get("email", "").strip().casefold()
    cargo = form.get("cargo", Cargo.OPERADOR).strip()
    ativo = form.get("ativo") == "on"
    senha = form.get("senha", "")
    erros = []

    if not nome or len(nome) > 120:
        erros.append("Informe um nome com até 120 caracteres.")
    if not email or len(email) > 254 or "@" not in email:
        erros.append("Informe um e-mail válido.")
    if cargo not in Cargo.OPCOES:
        erros.append("Selecione um cargo válido.")
    duplicado = db.session.scalar(db.select(User.id).where(User.email == email))
    if duplicado is not None and (usuario is None or duplicado != usuario.id):
        erros.append("Já existe uma conta com este e-mail.")
    if senha and len(senha) < 8:
        erros.append("A senha deve ter pelo menos 8 caracteres.")
    if incluir_senha and not senha:
        erros.append("A senha é obrigatória para novos usuários.")

    return {
        "nome": nome,
        "email": email,
        "cargo": cargo,
        "ativo": ativo,
        "senha": senha,
    }, erros


@usuarios_bp.get("/")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def listar():
    consulta = db.select(User).order_by(User.nome.asc())
    busca = request.args.get("q", "").strip()
    cargo = request.args.get("cargo", "").strip()
    status = request.args.get("status", "").strip()

    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(db.or_(User.nome.ilike(termo), User.email.ilike(termo)))
    if cargo in Cargo.OPCOES:
        consulta = consulta.where(User.cargo == cargo)
    if status == "ativo":
        consulta = consulta.where(User.ativo.is_(True))
    elif status == "inativo":
        consulta = consulta.where(User.ativo.is_(False))

    usuarios = db.session.scalars(consulta).all()
    return render_template(
        "usuarios/listar.html",
        usuarios=usuarios,
        cargos=Cargo.OPCOES,
        filtros={"q": busca, "cargo": cargo, "status": status},
    )


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def novo():
    if request.method == "POST":
        dados, erros = _ler_campos(request.form, incluir_senha=True)
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template(
                "usuarios/form.html",
                usuario=None,
                cargos=Cargo.OPCOES,
            ), 400

        usuario = User(
            nome=dados["nome"],
            email=dados["email"],
            cargo=dados["cargo"],
            ativo=dados["ativo"],
        )
        usuario.definir_senha(dados["senha"])
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível cadastrar: o e-mail já está em uso.", "error")
            return render_template(
                "usuarios/form.html",
                usuario=None,
                cargos=Cargo.OPCOES,
            ), 409
        flash("Usuário cadastrado com sucesso.", "success")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/form.html", usuario=None, cargos=Cargo.OPCOES)


@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def editar(usuario_id):
    usuario = db.get_or_404(User, usuario_id)
    if request.method == "POST":
        dados, erros = _ler_campos(request.form, usuario=usuario)
        preserva_admin = (
            usuario.cargo == Cargo.ADMINISTRADOR
            and usuario.ativo
            and _admins_ativos() <= 1
            and (dados["cargo"] != Cargo.ADMINISTRADOR or not dados["ativo"])
        )
        if preserva_admin:
            erros.append("O sistema precisa manter pelo menos um administrador ativo.")
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template(
                "usuarios/form.html",
                usuario=usuario,
                cargos=Cargo.OPCOES,
            ), 400

        usuario.nome = dados["nome"]
        usuario.email = dados["email"]
        usuario.cargo = dados["cargo"]
        usuario.ativo = dados["ativo"]
        if dados["senha"]:
            usuario.definir_senha(dados["senha"])
        db.session.commit()
        flash("Usuário atualizado com sucesso.", "success")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/form.html", usuario=usuario, cargos=Cargo.OPCOES)


@usuarios_bp.post("/<int:usuario_id>/excluir")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def excluir(usuario_id):
    usuario = db.get_or_404(User, usuario_id)
    if usuario.id == current_user.id:
        flash("Não é possível excluir sua própria conta nesta tela.", "error")
        return redirect(url_for("usuarios.listar"))
    if usuario.cargo == Cargo.ADMINISTRADOR and usuario.ativo and _admins_ativos() <= 1:
        flash("Não é possível excluir o último administrador ativo.", "error")
        return redirect(url_for("usuarios.listar"))

    for cruzamento in usuario.cruzamentos:
        cruzamento.usuario_id = None
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído com sucesso.", "success")
    return redirect(url_for("usuarios.listar"))
