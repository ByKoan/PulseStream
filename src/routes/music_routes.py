import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

from services.music_service import get_user_folder, get_user_songs
from utils.file_utils import allowed_file
from database.db import get_db_connection

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


@music_bp.route('/play/<filename>')
def play(filename):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_folder = get_user_folder(session['user_id'])
    file_path = os.path.join(user_folder, filename)

    if os.path.isfile(file_path) and allowed_file(filename):

        # =========================
        # Aumentar contador plays
        # =========================
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE songs
                SET plays = plays + 1
                WHERE filename = %s
                """,
                (filename,)
            )
            conn.commit()
        except Exception as e:
            print(f"Error al actualizar plays: {e}")
        finally:
            cursor.close()
            conn.close()

        return send_file(file_path)

    return "Archivo no encontrado", 404