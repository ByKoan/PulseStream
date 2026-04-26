import os  # Permite trabajar con rutas y el sistema operativo

from flask import Flask  # Clase principal para crear la app web con Flask
from config import Config  # Clase de configuración del proyecto
from dotenv import load_dotenv  # Para cargar variables desde el archivo .env

from database.db import create_user_db  # Función para crear/inicializar la base de datos de usuarios
from resources.sync_music_db import sync_music_database  # Sincroniza la base de datos de música

# Importación de blueprints (módulos de rutas organizados por funcionalidades)
from routes.auth_routes import auth_bp
from routes.music_routes import music_bp
from routes.upload_routes import upload_bp
from routes.admin_routes import admin_bp
from routes.playlist_routes import playlist_bp
from routes.add_to_playlist import add_playlist_bp
from routes.remove_from_playlist import remove_playlist_bp
from routes.youtube_page import youtube_bp

# Construye la ruta al archivo .env (en el mismo directorio que este archivo)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Carga las variables de entorno desde el archivo .env
load_dotenv(dotenv_path)


def create_app():
    # Crea la instancia principal de la aplicación Flask
    app = Flask(__name__)

    # Carga la configuración desde la clase Config
    app.config.from_object(Config)

    # Inicializa la base de datos de usuarios (si no existe, la crea)
    create_user_db()

    # Sincroniza la base de datos de música (por ejemplo, escaneando archivos o actualizando datos)
    sync_music_database()

    # Define la clave secreta usada para sesiones, cookies, etc.
    # Si no hay una en Config, usa una por defecto (no recomendable en producción)
    app.secret_key = Config.SECRET_KEY or "test_12345"

    # Registro de blueprints (cada uno añade rutas/endpoints a la app)
    app.register_blueprint(auth_bp)            # Rutas de autenticación (login, registro, etc.)
    app.register_blueprint(music_bp)           # Rutas relacionadas con música
    app.register_blueprint(upload_bp)          # Subida de archivos
    app.register_blueprint(admin_bp)           # Panel o funciones de administrador
    app.register_blueprint(playlist_bp)        # Gestión de playlists
    app.register_blueprint(add_playlist_bp)    # Añadir canciones a playlist
    app.register_blueprint(remove_playlist_bp) # Eliminar canciones de playlist
    app.register_blueprint(youtube_bp)         # Funcionalidades relacionadas con YouTube

    # Imprime todas las rutas disponibles en la aplicación (debug)
    print(app.url_map)

    # Devuelve la app ya configurada
    return app


# Crea la aplicación ejecutando la función anterior
app = create_app()

# Muestra la clave secreta en consola (útil para debug, pero peligroso en producción)
print("SECRET KEY = ", app.secret_key)


# Punto de entrada del programa
if __name__ == "__main__":
    # Ejecuta el servidor Flask
    # host="0.0.0.0" permite acceso desde otras máquinas
    # port=8080 define el puerto del servidor
    app.run(host="0.0.0.0", port=8080)