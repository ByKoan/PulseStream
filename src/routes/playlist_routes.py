from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, send_from_directory, session, abort
from database.db import get_db_connection

import os
import yt_dlp

from config import Config
from utils.file_utils import allowed_file

playlist_bp = Blueprint("playlist", __name__)


@playlist_bp.route("/playlists")
def playlists():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM playlists WHERE user_id = %s",
        (session["user_id"],)
    )

    playlists = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("playlists.html", playlists=playlists)


@playlist_bp.route("/create_playlist", methods=["POST"])
def create_playlist():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    name = request.form.get("name")

    if not name:
        return redirect(url_for("playlist.playlists"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO playlists (name, user_id) VALUES (%s,%s)",
        (name, session["user_id"])
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("playlist.playlists"))

@playlist_bp.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM playlists WHERE id=%s AND user_id=%s", 
                       (playlist_id, session['user_id']))
        playlist = cursor.fetchone()

        if not playlist:
            return redirect(url_for("playlist.playlists"))

        cursor.execute("""
            SELECT s.filename 
            FROM playlist_songs ps
            JOIN songs s ON ps.song_id = s.id
            WHERE ps.playlist_id = %s
        """, (playlist_id,))
        songs = [row['filename'] for row in cursor.fetchall()]

    finally:
        cursor.close()
        conn.close()

    return render_template("playlist_view.html", playlist=playlist, songs=songs)

@playlist_bp.route("/delete_playlist", methods=["POST"])
def delete_playlist():

    if "user_id" not in session:
        return jsonify({"success": False, "error": "No logueado"})

    data = request.get_json()
    playlist_id = data.get("playlist_id")

    if not playlist_id:
        return jsonify({"success": False, "error": "ID inválido"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id FROM playlists 
            WHERE id=%s AND user_id=%s
        """, (playlist_id, session["user_id"]))

        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"})

        cursor.execute(
            "DELETE FROM playlist_songs WHERE playlist_id=%s",
            (playlist_id,)
        )

        # [PERSONAL NOTE] Revisar si unicamente eliminando la playlist (por esquema de BD) se borran tb las canciones de la playlist en BD
        cursor.execute(
            "DELETE FROM playlists WHERE id=%s",
            (playlist_id,)
        )

        conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)})

    finally:
        cursor.close()
        conn.close()

@playlist_bp.route("/rename_playlist", methods=["POST"])
def rename_playlist():
    # [PERSONAL_NOTE] Arreglar que cuando tengas un nombre de playlist largo y lo quieras renombrar no se salgan los divs del div principal
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No logueado"})

    data = request.get_json()
    playlist_id = data.get("playlist_id")
    new_name = data.get("name")

    if not playlist_id or not new_name:
        return jsonify({"success": False, "error": "Datos inválidos"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )

        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"})

        cursor.execute(
            "UPDATE playlists SET name=%s WHERE id=%s",
            (new_name, playlist_id)
        )

        conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)})

    finally:
        cursor.close()
        conn.close()


@playlist_bp.route("/import_youtube_playlist", methods=["POST"])
def import_youtube_playlist():

    if "user_id" not in session:
        return jsonify({"success": False, "error": "No logueado"}), 401

    username = session.get("username")

    if not username:
        return jsonify({"success": False, "error": "Usuario no encontrado"}), 404

    data = request.get_json()
    youtube_url = data.get("url")

    if not youtube_url:
        return jsonify({"success": False, "error": "URL requerida"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # =========================
        # obtener info SIN descargar primero
        # =========================
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        playlist_title = info.get("title", "YouTube Playlist")

        # =========================
        # crear playlist en DB
        # =========================
        cursor.execute("""
            INSERT INTO playlists (name, user_id)
            VALUES (%s, %s)
        """, (playlist_title, username))

        playlist_id = cursor.lastrowid

        # =========================
        # carpeta usuario
        # =========================
        user_music_folder = os.path.join(
            Config.BASE_MUSIC_FOLDER,
            username
        )
        os.makedirs(user_music_folder, exist_ok=True)

        # =========================
        # opciones descarga
        # =========================
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(user_music_folder, "%(title)s.%(ext)s"),
            "noplaylist": False,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }

        downloaded = 0

        # =========================
        # descargar canciones
        # =========================
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(youtube_url, download=True)
            entries = info.get("entries", [])

            for entry in entries:

                if not entry:
                    continue

                title = entry.get("title")
                filename = f"{title}.mp3"

                if not title or not allowed_file(filename):
                    continue

                # -------------------------
                # insertar canción (si no existe)
                # -------------------------
                cursor.execute("""
                    SELECT id FROM songs
                    WHERE filename=%s AND uploaded_by=%s
                """, (filename, username))

                song = cursor.fetchone()

                if song:
                    song_id = song["id"]
                else:
                    cursor.execute("""
                        INSERT INTO songs (title, filename, uploaded_by)
                        VALUES (%s,%s,%s)
                    """, (title, filename, username))

                    song_id = cursor.lastrowid
                    downloaded += 1

                # -------------------------
                # vincular a playlist
                # -------------------------
                cursor.execute("""
                    INSERT INTO playlist_songs (playlist_id, song_id)
                    VALUES (%s, %s)
                """, (playlist_id, song_id))

        conn.commit()

        return jsonify({
            "success": True,
            "playlist_id": playlist_id,
            "downloaded": downloaded
        })

    except Exception as e:
        conn.rollback()
        current_app.logger.exception("Error importando playlist")
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# Need to fix play songs from playlist
@playlist_bp.route("/play/<path:filename>")
def play_song(filename):

    if "username" not in session:
        abort(401)

    username = session["username"]

    user_music_folder = os.path.join(
        Config.BASE_MUSIC_FOLDER,
        username
    )

    file_path = os.path.join(user_music_folder, filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(user_music_folder, filename)