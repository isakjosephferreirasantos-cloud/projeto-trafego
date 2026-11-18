from urllib.parse import urljoin, urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cargo, User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
GESTAO_CARGOS = {Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO}


def _safe_local_target(target):
    if not target:
        return None
    try:
        ref = urlsplit(urljoin(request.host_url, target))
        base = urlsplit(request.host_url)
    except ValueError:
        return None
    if ref.scheme in {"http", "https"} and ref.netloc == base.netloc:
        return target
    return None


def _home_for(usuario):
    if usuario.cargo in GESTAO_CARGOS:
        return url_for("main.dashboard")
    return url_for("site.public_home")


def _destination_after_auth(usuario, target):
    destino = _safe_local_target(target)
    if destino:
        caminho = urlsplit(urljoin(request.host_url, destino)).path
        if usuario.cargo not in GESTAO_CARGOS and caminho in {
            url_for("main.dashboard"),
            url_for("site.management_login"),
        }:
            return _home_for(usuario)
        return destino
    return _home_for(usuario)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_destination_after_auth(current_user, request.args.get("next")))

    if request.method == "POST":
        email = request.form.get("email", "").strip().casefold()
        senha = request.form.get("senha", "")
        usuario = db.session.scalar(db.select(User).where(User.email == email))

        if usuario is None or not usuario.ativo or not usuario.verificar_senha(senha):
            flash("E-mail ou senha inválidos.", "error")
            return render_template("auth/login.html"), 401

        login_user(usuario, remember=request.form.get("lembrar") == "on")
        flash("Login realizado com sucesso.", "success")
        return redirect(_destination_after_auth(usuario, request.args.get("next")))

    return render_template("auth/login.html")


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(_destination_after_auth(current_user, request.args.get("next")))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().casefold()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        erros = []
        if not nome or len(nome) > 120:
            erros.append("Informe um nome com até 120 caracteres.")
        if not email or len(email) > 254 or "@" not in email:
            erros.append("Informe um e-mail válido.")
        if len(senha) < 8:
            erros.append("A senha deve ter pelo menos 8 caracteres.")
        if senha != confirmar_senha:
            erros.append("As senhas não conferem.")
        if email and db.session.scalar(db.select(User.id).where(User.email == email)):
            erros.append("Já existe uma conta com este e-mail.")

        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template("auth/registro.html"), 400

        usuario = User(nome=nome, email=email, cargo=Cargo.OPERADOR, ativo=True)
        usuario.definir_senha(senha)
        db.session.add(usuario)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe uma conta com este e-mail.", "error")
            return render_template("auth/registro.html"), 409

        login_user(usuario)
        flash("Cadastro realizado. Bem-vindo ao sistema.", "success")
        return redirect(_destination_after_auth(usuario, request.args.get("next")))

    return render_template("auth/registro.html")


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("auth.login"))
