import os
from config import Config
from utils.file_utils import allowed_file

def get_user_folder(user_id):

    user_folder = os.path.join(Config.BASE_MUSIC_FOLDER, user_id)
    os.makedirs(user_folder, exist_ok=True)

    return user_folder


def get_user_songs(user_id, query=None):

    user_folder = get_user_folder(user_id)

    songs = [f for f in os.listdir(user_folder) if allowed_file(f)]

    if query:
        query = query.lower()
        songs = [song for song in songs if query in song.lower()]

    return songs