from flask import Flask
from config import Config
from database.db import create_user_db
from routes.auth_routes import auth_bp
from routes.music_routes import music_bp


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    app.secret_key = Config.SECRET_KEY

    app.register_blueprint(auth_bp)
    app.register_blueprint(music_bp)

    return app


app = create_app()

if __name__ == "__main__":

    create_user_db()

    app.run(host="0.0.0.0", port=5000)