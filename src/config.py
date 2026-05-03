import os

# Clase de configuración central de la aplicación
# Todos los valores se leen desde variables de entorno, con fallbacks por defecto
class Config:

    # Clave secreta para firmar sesiones y cookies de Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "test_12345")

    # Credenciales de conexión a MySQL
    DB_USER     = os.getenv("DB_USER",     "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME     = os.getenv("DB_NAME",     "music_db")
    DB_HOST     = os.getenv("DB_HOST",     "db")

    # Ruta raíz donde se almacenan los archivos de música de los usuarios
    # Cada usuario tiene su propia subcarpeta: BASE_MUSIC_FOLDER/<username>/
    BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")

    # Extensiones de audio permitidas para subir o reproducir
    ALLOWED_EXTENSIONS = {
        # Formatos estándar y más compatibles
        'mp3', 'm4a', 'wav',

        # Formatos de alta eficiencia y Apple
        'aac', 'alac',

        # Formatos Libres / Open Source (Muy recomendados para web)
        'ogg', 'oga', 'opus',

        # Formatos sin pérdida (Lossless)
        'flac', 'aiff', 'dsd'
    }