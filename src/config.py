import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")

    BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER")

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