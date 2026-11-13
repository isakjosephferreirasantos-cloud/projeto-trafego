import os

from app import create_app
from extensions import db
from models import Cargo, Congestionamento, Cruzamento, TipoIntersecao, User


ADMIN_EMAIL = "admserra@gmail.com"
ADMIN_PASSWORD_ENV = "SIMULATOR_ADMIN_PASSWORD"
LEGACY_ADMIN_EMAIL = "admin@simulador.local"


def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()

        admin = db.session.scalar(db.select(User).where(User.email == ADMIN_EMAIL))
        if admin is None:
            admin = db.session.scalar(
                db.select(User).where(User.email == LEGACY_ADMIN_EMAIL)
            )
            if admin is not None:
                admin.email = ADMIN_EMAIL

        if admin is None:
            admin_password = os.environ.get(ADMIN_PASSWORD_ENV)
            if not admin_password:
                raise RuntimeError(
                    f"Defina a variável de ambiente {ADMIN_PASSWORD_ENV} "
                    "para criar a conta de administrador."
                )
            admin = User(
                nome="Administrador",
                email=ADMIN_EMAIL,
                cargo=Cargo.ADMINISTRADOR,
                ativo=True,
            )
            admin.definir_senha(admin_password)
            db.session.add(admin)
            db.session.flush()

        exemplos = (
            {
                "nome": "Cruzamento Principal",
                "tipo_intersecao": TipoIntersecao.SEMAFORO,
                "tempo_verde": 30,
                "tempo_vermelho": 30,
                "onda_verde": False,
                "tempo_espera_medio": 45.0,
                "congestionamento": Congestionamento.MEDIO,
                "veiculos_minuto": 18,
            },
            {
                "nome": "Avenida Central",
                "tipo_intersecao": TipoIntersecao.ROTATORIA,
                "tempo_verde": 25,
                "tempo_vermelho": 25,
                "onda_verde": False,
                "tempo_espera_medio": 30.0,
                "congestionamento": Congestionamento.BAIXO,
                "veiculos_minuto": 12,
            },
        )

        for dados in exemplos:
            existente = db.session.scalar(
                db.select(Cruzamento).where(Cruzamento.nome == dados["nome"])
            )
            if existente is None:
                db.session.add(Cruzamento(**dados, usuario_id=admin.id))

        db.session.commit()
        print(f"Banco inicializado: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Usuário administrador: {ADMIN_EMAIL}")
        print("Os valores dos cruzamentos são exemplos para simulação, não medições de tráfego.")


if __name__ == "__main__":
    seed_database()
