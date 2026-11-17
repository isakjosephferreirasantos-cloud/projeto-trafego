import os

from flask import Flask

from config import Config
from extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    from routes import register_blueprints

    register_blueprints(app)
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        from models import User

        try:
            parsed_user_id = int(user_id)
        except (TypeError, ValueError):
            return None
        return db.session.get(User, parsed_user_id)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "").casefold() == "1",
    )
