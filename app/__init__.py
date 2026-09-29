from flask import Flask
from app.routes import main


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = "mcmt-secret-key"

    app.register_blueprint(main)

    return app