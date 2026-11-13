from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cargo, Congestionamento, Cruzamento, TipoIntersecao
from routes.decorators import cargos_permitidos


cruzamentos_bp = Blueprint("cruzamentos", __name__)


def _dados_cruzamento(form):
    erros = []
    dados = {}
    dados["nome"] = str(form.get("nome", "")).strip()
    dados["tipo_intersecao"] = str(
        form.get("tipo_intersecao", TipoIntersecao.SEMAFORO)
    ).strip()
    dados["congestionamento"] = str(
        form.get("congestionamento", Congestionamento.MEDIO)
    ).strip().upper()
    dados["onda_verde"] = form.get("onda_verde") in {True, "true", "1", "on", 1}

    if not dados["nome"] or len(dados["nome"]) > 120:
        erros.append("Informe um nome com até 120 caracteres.")
    if dados["tipo_intersecao"] not in TipoIntersecao.OPCOES:
        erros.append("Selecione um tipo de interseção válido.")
    if dados["congestionamento"] not in Congestionamento.OPCOES:
        erros.append("Selecione um nível de congestionamento válido.")

    for campo, minimo, maximo in (
        ("tempo_verde", 0, 3600),
        ("tempo_vermelho", 0, 3600),
        ("veiculos_minuto", 0, 100000),
    ):
        try:
            dados[campo] = int(form.get(campo, ""))
            if not minimo <= dados[campo] <= maximo:
                raise ValueError
        except (TypeError, ValueError):
            erros.append(f"Informe um valor válido para {campo.replace('_', ' ')}.")

    try:
        dados["tempo_espera_medio"] = float(form.get("tempo_espera_medio", ""))
        if not 0 <= dados["tempo_espera_medio"] <= 86400:
            raise ValueError
    except (TypeError, ValueError):
        erros.append("Informe um tempo de espera entre 0 e 86400 segundos.")

    return dados, erros


def _resposta_erro(erros, status=400):
    if request.is_json:
        return jsonify(error=" ".join(erros), errors=erros), status
    for erro in erros:
        flash(erro, "error")
    return None


@cruzamentos_bp.get("/")
@login_required
def listar():
    consulta = db.select(Cruzamento).order_by(Cruzamento.nome.asc())
    nome = request.args.get("nome", "").strip()
    tipo = request.args.get("tipo_intersecao", "").strip()
    congestionamento = request.args.get("congestionamento", "").strip().upper()

    if nome:
        consulta = consulta.where(Cruzamento.nome.ilike(f"%{nome}%"))
    if tipo in TipoIntersecao.OPCOES:
        consulta = consulta.where(Cruzamento.tipo_intersecao == tipo)
    if congestionamento in Congestionamento.OPCOES:
        consulta = consulta.where(Cruzamento.congestionamento == congestionamento)

    cruzamentos = db.session.scalars(consulta).all()
    return render_template(
        "cruzamentos/listar.html",
        cruzamentos=cruzamentos,
        tipos=TipoIntersecao.OPCOES,
        niveis=Congestionamento.OPCOES,
        filtros={
            "nome": nome,
            "tipo_intersecao": tipo,
            "congestionamento": congestionamento,
        },
    )


@cruzamentos_bp.route("/novo", methods=["GET", "POST"])
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def novo():
    if request.method == "POST":
        dados, erros = _dados_cruzamento(request.form)
        if erros:
            _resposta = _resposta_erro(erros)
            if _resposta is not None:
                return _resposta
            return render_template(
                "cruzamentos/form.html",
                cruzamento=None,
                tipos=TipoIntersecao.OPCOES,
                niveis=Congestionamento.OPCOES,
            ), 400

        cruzamento = Cruzamento(**dados, usuario_id=current_user.id)
        db.session.add(cruzamento)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Não foi possível salvar o cruzamento.", "error")
            return render_template(
                "cruzamentos/form.html",
                cruzamento=None,
                tipos=TipoIntersecao.OPCOES,
                niveis=Congestionamento.OPCOES,
            ), 400
        flash("Cruzamento cadastrado com sucesso.", "success")
        return redirect(url_for("cruzamentos.listar"))

    return render_template(
        "cruzamentos/form.html",
        cruzamento=None,
        tipos=TipoIntersecao.OPCOES,
        niveis=Congestionamento.OPCOES,
    )


@cruzamentos_bp.route("/<int:cruzamento_id>/editar", methods=["GET", "POST"])
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def editar(cruzamento_id):
    cruzamento = db.get_or_404(Cruzamento, cruzamento_id)
    if request.method == "POST":
        dados, erros = _dados_cruzamento(request.form)
        if erros:
            _resposta = _resposta_erro(erros)
            if _resposta is not None:
                return _resposta
            return render_template(
                "cruzamentos/form.html",
                cruzamento=cruzamento,
                tipos=TipoIntersecao.OPCOES,
                niveis=Congestionamento.OPCOES,
            ), 400
        for campo, valor in dados.items():
            setattr(cruzamento, campo, valor)
        cruzamento.usuario_id = current_user.id
        db.session.commit()
        flash("Cruzamento atualizado com sucesso.", "success")
        return redirect(url_for("cruzamentos.listar"))

    return render_template(
        "cruzamentos/form.html",
        cruzamento=cruzamento,
        tipos=TipoIntersecao.OPCOES,
        niveis=Congestionamento.OPCOES,
    )


@cruzamentos_bp.get("/<int:cruzamento_id>/simulador")
@login_required
def simulador(cruzamento_id):
    cruzamento = db.get_or_404(Cruzamento, cruzamento_id)
    return render_template("cruzamentos/simulador.html", cruzamento=cruzamento)


@cruzamentos_bp.post("/<int:cruzamento_id>/simulacao")
@login_required
def salvar_simulacao(cruzamento_id):
    cruzamento = db.get_or_404(Cruzamento, cruzamento_id)
    dados_recebidos = request.get_json(silent=False)
    if not isinstance(dados_recebidos, dict):
        return jsonify(error="Envie os dados da simulação como objeto JSON."), 400

    dados, erros = _dados_cruzamento({
        **dados_recebidos,
        "nome": cruzamento.nome,
    })
    if erros:
        return _resposta_erro(erros)

    cruzamento.tipo_intersecao = dados["tipo_intersecao"]
    cruzamento.tempo_verde = dados["tempo_verde"]
    cruzamento.tempo_vermelho = dados["tempo_vermelho"]
    cruzamento.onda_verde = dados["onda_verde"]
    cruzamento.tempo_espera_medio = dados["tempo_espera_medio"]
    cruzamento.congestionamento = dados["congestionamento"]
    cruzamento.veiculos_minuto = dados["veiculos_minuto"]
    if current_user.cargo in {Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO}:
        cruzamento.usuario_id = current_user.id
    db.session.commit()
    return jsonify(
        message="Resultados da simulação salvos.",
        cruzamento_id=cruzamento.id,
        tempo_espera_medio=cruzamento.tempo_espera_medio,
        congestionamento=cruzamento.congestionamento,
        veiculos_minuto=cruzamento.veiculos_minuto,
    )


@cruzamentos_bp.post("/<int:cruzamento_id>/excluir")
@login_required
@cargos_permitidos(Cargo.ADMINISTRADOR, Cargo.ENGENHEIRO)
def excluir(cruzamento_id):
    cruzamento = db.get_or_404(Cruzamento, cruzamento_id)
    db.session.delete(cruzamento)
    db.session.commit()
    flash("Cruzamento excluído com sucesso.", "success")
    return redirect(url_for("cruzamentos.listar"))
