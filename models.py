from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class Cargo:
    ADMINISTRADOR = "Administrador"
    ENGENHEIRO = "Engenheiro"
    OPERADOR = "Operador"
    OPCOES = (ADMINISTRADOR, ENGENHEIRO, OPERADOR)


class TipoIntersecao:
    SEMAFORO = "Semaforo"
    ROTATORIA = "Rotatoria"
    OPCOES = (SEMAFORO, ROTATORIA)


class Congestionamento:
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    BAIXO = "BAIXO"
    OPCOES = (ALTO, MEDIO, BAIXO)


class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    cargo = db.Column(db.String(20), nullable=False, default=Cargo.OPERADOR)
    password_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    cruzamentos = db.relationship("Cruzamento", back_populates="usuario")

    @property
    def is_active(self):
        return self.ativo

    def definir_senha(self, senha):
        if not isinstance(senha, str) or not senha:
            raise ValueError("A senha não pode ficar vazia.")
        self.password_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        if not isinstance(senha, str) or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, senha)


class Publicacao(db.Model):
    __tablename__ = "publicacoes"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    criada_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class Cruzamento(db.Model):
    __tablename__ = "cruzamentos"
    __table_args__ = (
        db.CheckConstraint("tempo_verde >= 0", name="ck_cruzamentos_tempo_verde"),
        db.CheckConstraint("tempo_vermelho >= 0", name="ck_cruzamentos_tempo_vermelho"),
        db.CheckConstraint("tempo_espera_medio >= 0", name="ck_cruzamentos_espera"),
        db.CheckConstraint("veiculos_minuto >= 0", name="ck_cruzamentos_veiculos"),
        db.CheckConstraint(
            "tipo_intersecao IN ('Semaforo', 'Rotatoria')",
            name="ck_cruzamentos_tipo_intersecao",
        ),
        db.CheckConstraint(
            "congestionamento IN ('ALTO', 'MEDIO', 'BAIXO')",
            name="ck_cruzamentos_congestionamento",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, index=True)
    tipo_intersecao = db.Column(db.String(20), nullable=False, default=TipoIntersecao.SEMAFORO)
    tempo_verde = db.Column(db.Integer, nullable=False, default=30)
    tempo_vermelho = db.Column(db.Integer, nullable=False, default=30)
    onda_verde = db.Column(db.Boolean, nullable=False, default=False)
    tempo_espera_medio = db.Column(db.Float, nullable=False, default=0.0)
    congestionamento = db.Column(db.String(10), nullable=False, default=Congestionamento.MEDIO)
    veiculos_minuto = db.Column(db.Integer, nullable=False, default=0)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    criado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atualizado_em = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    usuario = db.relationship("User", back_populates="cruzamentos")
