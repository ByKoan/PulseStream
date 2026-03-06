import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "test_12345")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "music_db")
    DB_HOST = os.getenv("DB_HOST", "db")
    BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")

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