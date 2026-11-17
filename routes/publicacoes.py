from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Cargo, Publicacao
from routes.decorators import cargos_permitidos


publicacoes_bp = Blueprint("publicacoes", __name__, url_prefix="/publicacoes")


def _listar_publicacoes():
    return db.session.scalars(
        db.select(Publicacao).order_by(Publicacao.criada_em.desc(), Publicacao.id.desc())
    ).all()


@publicacoes_bp.route("/", methods=["GET", "POST"])
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def listar():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        texto = request.form.get("texto", "").strip()
        erros = []
        if not titulo or len(titulo) > 120:
            erros.append("Informe um título com até 120 caracteres.")
        if not texto or len(texto) > 10000:
            erros.append("Informe um texto com até 10.000 caracteres.")

        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template(
                "publicacoes/listar.html",
                publicacoes=_listar_publicacoes(),
                titulo=titulo,
                texto=texto,
            ), 400

        db.session.add(Publicacao(titulo=titulo, texto=texto))
        db.session.commit()
        flash("Atualização publicada no site.", "success")
        return redirect(url_for("publicacoes.listar"))

    return render_template(
        "publicacoes/listar.html",
        publicacoes=_listar_publicacoes(),
        titulo="",
        texto="",
    )


@publicacoes_bp.post("/<int:publicacao_id>/excluir")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR)
def excluir(publicacao_id):
    publicacao = db.get_or_404(Publicacao, publicacao_id)
    db.session.delete(publicacao)
    db.session.commit()
    flash("Atualização removida do site.", "success")
    return redirect(url_for("publicacoes.listar"))
