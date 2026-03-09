import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, jsonify
from werkzeug.utils import secure_filename

from services.music_service import get_user_folder, get_user_songs
from utils.file_utils import allowed_file
from database.db import get_db_connection
from config import Config  

music_bp = Blueprint("music", __name__)


@music_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener canciones
    cursor.execute("SELECT filename FROM songs")
    songs = [row['filename'] for row in cursor.fetchall()]

    # Obtener playlists del usuario
    cursor.execute("SELECT id, name FROM playlists WHERE user_id = %s", (session["user_id"],))
    playlists = cursor.fetchall()

    cursor.close()
    conn.close()

    # Pasar playlists a la plantilla
    return render_template("index.html", songs=songs, current_song="", playlists=playlists)


@music_bp.route('/play/<filename>')
def play(filename):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_folder = get_user_folder(session['user_id'])
    file_path = os.path.join(user_folder, filename)

    if os.path.isfile(file_path) and allowed_file(filename):
        # Aumentar contador de reproducciones
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE songs SET plays = plays + 1 WHERE filename = %s",
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


@music_bp.route("/delete_song", methods=["POST"])
def delete_song():
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    filename = data.get("filename")

    if not filename or not allowed_file(filename):
        return jsonify({"error": "Archivo no válido"}), 400

    # Ruta absoluta del archivo en la carpeta del usuario
    filepath = os.path.join(get_user_folder(session['user_id']), filename)

    # Borrar de la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM songs WHERE filename=%s", (filename,))
        conn.commit()
    except Exception as e:
        return jsonify({"error": f"No se pudo borrar de la BD: {e}"}), 500
    finally:
        cursor.close()
        conn.close()

    # Borrar del disco
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            return jsonify({"error": f"No se pudo borrar del disco: {e}"}), 500

    return jsonify({"success": True})