import csv
from datetime import datetime
from io import BytesIO, StringIO

from flask import Blueprint, make_response, render_template, request
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from extensions import db
from models import Cargo, Congestionamento, Cruzamento, TipoIntersecao
from routes.decorators import cargos_permitidos


relatorios_bp = Blueprint("relatorios", __name__)


def _filtrar_cruzamentos():
    consulta = db.select(Cruzamento).order_by(Cruzamento.nome.asc())
    nome = request.args.get("nome", "").strip()
    tipo = request.args.get("tipo_intersecao", "").strip()
    nivel = request.args.get("congestionamento", "").strip().upper()

    if nome:
        consulta = consulta.where(Cruzamento.nome.ilike(f"%{nome}%"))
    if tipo in TipoIntersecao.OPCOES:
        consulta = consulta.where(Cruzamento.tipo_intersecao == tipo)
    if nivel in Congestionamento.OPCOES:
        consulta = consulta.where(Cruzamento.congestionamento == nivel)

    return db.session.scalars(consulta).all()


def _criar_csv(cruzamentos):
    arquivo = StringIO(newline="")
    escritor = csv.writer(arquivo, delimiter=";")
    escritor.writerow(
        [
            "Nome",
            "Tipo de interseção",
            "Tempo verde (s)",
            "Tempo vermelho (s)",
            "Onda verde",
            "Espera média (s)",
            "Congestionamento",
            "Veículos por minuto",
        ]
    )
    for cruzamento in cruzamentos:
        escritor.writerow(
            [
                cruzamento.nome,
                cruzamento.tipo_intersecao,
                cruzamento.tempo_verde,
                cruzamento.tempo_vermelho,
                "Sim" if cruzamento.onda_verde else "Não",
                f"{cruzamento.tempo_espera_medio:.2f}",
                cruzamento.congestionamento,
                cruzamento.veiculos_minuto,
            ]
        )
    response = make_response("\ufeff" + arquivo.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="relatorio-cruzamentos.csv"'
    return response


def _criar_pdf(cruzamentos):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Relatório de cruzamentos",
        author="Simulador de Fluxo Urbano",
    )
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#176b4b"),
        spaceAfter=8,
    )
    subtitulo = ParagraphStyle(
        "SubtituloRelatorio",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526056"),
        spaceAfter=14,
    )
    conteudo = [
        Paragraph("Relatório de cruzamentos", titulo),
        Paragraph(
            f"Gerado em {datetime.now().astimezone().strftime('%d/%m/%Y às %H:%M')} "
            f"· {len(cruzamentos)} registro(s)",
            subtitulo,
        ),
    ]

    cabecalho = [
        "Nome",
        "Interseção",
        "Verde (s)",
        "Vermelho (s)",
        "Onda verde",
        "Espera (s)",
        "Congestionamento",
        "Veículos/min",
    ]
    linhas = [cabecalho]
    for item in cruzamentos:
        linhas.append(
            [
                Paragraph(item.nome, estilos["BodyText"]),
                item.tipo_intersecao,
                str(item.tempo_verde),
                str(item.tempo_vermelho),
                "Sim" if item.onda_verde else "Não",
                f"{item.tempo_espera_medio:.1f}",
                item.congestionamento,
                str(item.veiculos_minuto),
            ]
        )
    tabela = Table(
        linhas,
        repeatRows=1,
        colWidths=[48 * mm, 27 * mm, 17 * mm, 20 * mm, 22 * mm, 20 * mm, 31 * mm, 23 * mm],
        hAlign="LEFT",
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#252c34")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd3cc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f1")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    conteudo.extend([Spacer(1, 4), tabela])
    documento.build(conteudo)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = 'attachment; filename="relatorio-cruzamentos.pdf"'
    return response


@relatorios_bp.get("/")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def index():
    cruzamentos = _filtrar_cruzamentos()
    filtros = {
        "nome": request.args.get("nome", "").strip(),
        "tipo_intersecao": request.args.get("tipo_intersecao", "").strip(),
        "congestionamento": request.args.get("congestionamento", "").strip().upper(),
    }
    return render_template(
        "relatorios/index.html",
        cruzamentos=cruzamentos,
        filtros=filtros,
        tipos=TipoIntersecao.OPCOES,
        niveis=Congestionamento.OPCOES,
    )


@relatorios_bp.get("/csv")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def exportar_csv():
    return _criar_csv(_filtrar_cruzamentos())


@relatorios_bp.get("/pdf")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def exportar_pdf():
    return _criar_pdf(_filtrar_cruzamentos())
