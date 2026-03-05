import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

from services.music_service import get_user_folder, get_user_songs
from utils.file_utils import allowed_file

music_bp = Blueprint("music", __name__)


@music_bp.route('/')
def index():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    songs = get_user_songs(session['user_id'])

    query = request.args.get('search', '').strip()

    if query:
        songs = get_user_songs(session['user_id'], query)

    current_song = songs[0] if songs else "No hay canciones"

    return render_template("index.html", songs=songs, current_song=current_song)


@music_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_folder = get_user_folder(session['user_id'])

    if request.method == 'POST':

        if 'file' not in request.files:
            return "No se envió ningún archivo", 400

        files = request.files.getlist('file')

        for file in files:

            if file.filename == '':
                continue

            if file and allowed_file(file.filename):

                filename = secure_filename(file.filename)

                file.save(os.path.join(user_folder, filename))

        return redirect(url_for('music.index'))

    return "Sube tus archivos aquí."


@music_bp.route('/play/<filename>')
def play(filename):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_folder = get_user_folder(session['user_id'])

    file_path = os.path.join(user_folder, filename)

    if os.path.isfile(file_path) and allowed_file(filename):
        return send_file(file_path)

    return "Archivo no encontrado", 404