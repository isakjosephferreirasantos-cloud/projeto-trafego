import json
from datetime import timezone
from pathlib import Path

from flask import Blueprint, Response, flash, jsonify, redirect, request, send_from_directory, url_for
from flask_login import current_user

from extensions import db
from models import Cargo, Publicacao


site_bp = Blueprint("site", __name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAFFIC_PAGE = PROJECT_ROOT / "html" / "trafego.html"
SIMULATOR_JS = Path(__file__).resolve().parents[1] / "static" / "js"


@site_bp.before_request
def require_registration_for_public_site():
    protected_endpoints = {
        "site.public_home",
        "site.public_posts",
        "site.simulator_script",
    }
    if request.endpoint in protected_endpoints and not current_user.is_authenticated:
        next_url = request.full_path.rstrip("?")
        return redirect(url_for("auth.registro", next=next_url))


DEFAULT_STUDY_POINTS = (
    {
        "id": 1,
        "title": "Centro · fluxo na rotatória",
        "place": "Entorno da área central",
        "type": "rotatoria",
        "coords": [-7.9827, -38.2894],
        "note": "Verificar se a geometria do cruzamento comporta uma rotatória com segurança e sem prejudicar pedestres e acessos.",
    },
    {
        "id": 2,
        "title": "Eixo comercial · filas no semáforo",
        "place": "Referência aproximada no Centro",
        "type": "tempo",
        "coords": [-7.9786, -38.2928],
        "note": "Investigar se há filas recorrentes e se os tempos semafóricos acompanham o fluxo por horário.",
    },
    {
        "id": 3,
        "title": "Acesso urbano · travessias e conversões",
        "place": "Conexão com vias de maior movimento",
        "type": "seguranca",
        "coords": [-7.9865, -38.2977],
        "note": "Observar conflitos entre veículos e pedestres e avaliar a segurança das travessias e conversões.",
    },
    {
        "id": 4,
        "title": "Corredor · espera semafórica",
        "place": "Ponto de referência para contagens",
        "type": "tempo",
        "coords": [-7.9765, -38.2847],
        "note": "Medir tempos de espera por faixa horária antes de afirmar que o ciclo semafórico precisa de ajuste.",
    },
)


@site_bp.get("/")
def public_home():
    template = TRAFFIC_PAGE.read_text(encoding="utf-8")
    template = template.replace('href="#admin"', 'href="/admin"')
    template = template.replace(
        'window.addEventListener("hashchange", handleAdminRoute);\n'
        '        startPresenceHeartbeat();\n'
        '        loadPosts();\n'
        '        handleAdminRoute();',
        'window.addEventListener("hashchange", () => {\n'
        '            if (location.hash === "#admin") window.location.assign("/admin");\n'
        '        });\n'
        '        loadPosts();\n'
        '        if (location.hash === "#admin") window.location.replace("/admin");',
    )
    template = template.replace(
        "O monitoramento administrativo usa identificador temporário por aba, sem armazenar IP, "
        "e expira após 5 minutos sem atividade.",
        "A área de gestão exige autenticação; as simulações são educativas e não substituem estudos de campo.",
    )
    points = json.dumps(DEFAULT_STUDY_POINTS, ensure_ascii=False)
    points = points.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return Response(
        template.replace("__STUDY_POINTS_JSON__", points),
        content_type="text/html; charset=utf-8",
    )


@site_bp.get("/admin")
def management_login():
    if current_user.is_authenticated:
        if current_user.cargo not in {Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO}:
            flash("A área de gestão é restrita à equipe autorizada.", "error")
            return redirect(url_for("site.public_home"))
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login", next=url_for("main.dashboard")))


@site_bp.get("/assets/simulador3d.js")
def simulator_script():
    return send_from_directory(SIMULATOR_JS, "simulador3d.js")


@site_bp.get("/api/posts")
def public_posts():
    publicacoes = db.session.scalars(
        db.select(Publicacao).order_by(Publicacao.criada_em.desc(), Publicacao.id.desc()).limit(12)
    ).all()
    posts = []
    for publicacao in publicacoes:
        criada_em = publicacao.criada_em
        if criada_em.tzinfo is None:
            criada_em = criada_em.replace(tzinfo=timezone.utc)
        posts.append(
            {
                "id": publicacao.id,
                "title": publicacao.titulo,
                "body": publicacao.texto,
                "image_url": "",
                "created_at": criada_em.isoformat(),
            }
        )
    return jsonify(posts=posts)
