import os  # Para trabajar con rutas y archivos del sistema
from config import Config  # Configuración del proyecto (rutas base, etc.)
from utils.file_utils import allowed_file  # Función que valida extensiones de archivos

def get_user_folder(user_id):
    # Construye la ruta a la carpeta del usuario:
    # Ejemplo: BASE_MUSIC_FOLDER/123
    user_folder = os.path.join(Config.BASE_MUSIC_FOLDER, user_id)

    # Crea la carpeta si no existe
    # exist_ok=True evita error si ya está creada
    os.makedirs(user_folder, exist_ok=True)

    # Devuelve la ruta de la carpeta del usuario
    return user_folder


def get_user_songs(user_id, query=None):
    # Obtiene (y asegura que exista) la carpeta del usuario
    user_folder = get_user_folder(user_id)

    # Lista todos los archivos de la carpeta
    # y filtra solo los que son válidos (audio, por ejemplo)
    songs = [f for f in os.listdir(user_folder) if allowed_file(f)]

    # Si se proporciona un texto de búsqueda (query)
    if query:
        # Convierte la búsqueda a minúsculas para comparación sin distinguir mayúsculas
        query = query.lower()

        # Filtra las canciones que contienen ese texto en su nombre
        songs = [song for song in songs if query in song.lower()]

    # Devuelve la lista final de canciones
    return songs