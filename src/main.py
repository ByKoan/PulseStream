from flask import Flask
from config import Config
from database.db import create_user_db
from routes.auth_routes import auth_bp
from routes.music_routes import music_bp
from routes.upload_routes import upload_bp
from routes.admin_routes import admin_bp
from routes.playlist_routes import playlist_bp
from routes.add_to_playlist import add_playlist_bp
from resources.sync_music_db import sync_music_database
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    create_user_db()
    sync_music_database()

    app.secret_key = Config.SECRET_KEY or "test_12345"

    app.register_blueprint(auth_bp)
    app.register_blueprint(music_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(playlist_bp)
    app.register_blueprint(add_playlist_bp)

    return app

app = create_app()
print("SECRET KEY = ", app.secret_key)

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080)