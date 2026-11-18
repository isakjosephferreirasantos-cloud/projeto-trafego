from flask import Blueprint, render_template
from flask_login import current_user, login_required

from extensions import db
from models import Cargo, Cruzamento, Congestionamento, User
from routes.decorators import cargos_permitidos


main_bp = Blueprint("main", __name__)


@main_bp.get("/painel")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def dashboard():
    total_cruzamentos = db.session.scalar(db.select(db.func.count(Cruzamento.id))) or 0
    total_usuarios = db.session.scalar(db.select(db.func.count(User.id))) or 0
    usuarios_cadastrados = []
    if current_user.cargo == Cargo.ADMINISTRADOR:
        usuarios_cadastrados = db.session.scalars(
            db.select(User.nome).order_by(User.nome.asc())
        ).all()
    alto = db.session.scalar(
        db.select(db.func.count(Cruzamento.id)).where(
            Cruzamento.congestionamento == Congestionamento.ALTO
        )
    ) or 0
    recentes = db.session.scalars(
        db.select(Cruzamento).order_by(Cruzamento.atualizado_em.desc()).limit(5)
    ).all()
    return render_template(
        "dashboard.html",
        total_cruzamentos=total_cruzamentos,
        total_usuarios=total_usuarios,
        usuarios_cadastrados=usuarios_cadastrados,
        congestionamento_alto=alto,
        cruzamentos_recentes=recentes,
    )


def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.cruzamentos import cruzamentos_bp
    from routes.publicacoes import publicacoes_bp
    from routes.relatorios import relatorios_bp
    from routes.site import site_bp
    from routes.usuarios import usuarios_bp

    app.register_blueprint(site_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    app.register_blueprint(publicacoes_bp)
    app.register_blueprint(cruzamentos_bp, url_prefix="/cruzamentos")
    app.register_blueprint(relatorios_bp, url_prefix="/relatorios")
