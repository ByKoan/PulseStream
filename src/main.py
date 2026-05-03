import os

from flask import Flask
from config import Config
from dotenv import load_dotenv

from database.db import create_user_db
from resources.sync_music_db import sync_music_database

# Blueprints: cada módulo agrupa las rutas de una funcionalidad concreta
from routes.auth_routes import auth_bp
from routes.music_routes import music_bp
from routes.upload_routes import upload_bp
from routes.admin_routes import admin_bp
from routes.playlist_routes import playlist_bp
from routes.add_to_playlist import add_playlist_bp
from routes.remove_from_playlist import remove_playlist_bp
from routes.youtube_page import youtube_bp

# Ruta al .env (mismo directorio que este archivo)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


def create_app():
    # Instancia principal de Flask
    app = Flask(__name__)

    # Carga SECRET_KEY, rutas, permisos, etc.
    app.config.from_object(Config)

    # Crea las tablas de la base de datos si todavía no existen
    create_user_db()

    # Compara los archivos en disco con los registros de la BD y los sincroniza
    sync_music_database()

    # Si Config no trae clave secreta se usa un valor de fallback
    # (en producción esto debería venir siempre del .env)
    app.secret_key = Config.SECRET_KEY or "test_12345"

    # Registro de blueprints — cada uno añade su grupo de rutas a la app
    app.register_blueprint(auth_bp)             # /login, /register, /logout
    app.register_blueprint(music_bp)            # /, /play/<filename>, /delete_song
    app.register_blueprint(upload_bp)           # /upload
    app.register_blueprint(admin_bp)            # /admin/*
    app.register_blueprint(playlist_bp)         # /playlists, /playlist/<id>, ...
    app.register_blueprint(add_playlist_bp)     # /add_to_playlist
    app.register_blueprint(remove_playlist_bp)  # /remove_from_playlist
    app.register_blueprint(youtube_bp)          # /youtube_page, /youtube_search, ...

    # Muestra el mapa de URLs disponibles (útil para debug)
    print(app.url_map)

    return app


# Crea la app al importar el módulo
app = create_app()

print("SECRET KEY = ", app.secret_key)


if __name__ == "__main__":
    # Escucha en todas las interfaces para ser accesible desde la red local
    app.run(host="0.0.0.0", port=8080)