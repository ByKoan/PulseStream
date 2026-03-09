from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection

add_playlist_bp = Blueprint("add_playlist", __name__)

@add_playlist_bp.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    data = request.get_json()
    filename = data.get("filename")
    playlist_id = data.get("playlist_id")

    if not filename or not playlist_id:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verificar que la playlist pertenece al usuario
        cursor.execute("SELECT id FROM playlists WHERE id = %s AND user_id = %s",
                       (playlist_id, session["user_id"]))
        playlist = cursor.fetchone()
        if not playlist:
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        # Verificar que la canción no esté ya en la playlist
        cursor.execute(
            "SELECT id FROM playlist_songs WHERE playlist_id = %s AND song_filename = %s",
            (playlist_id, filename)
        )
        if cursor.fetchone():
            return jsonify({"success": False, "error": "La canción ya está en la playlist"}), 409

        # Insertar la canción en la playlist
        cursor.execute(
            "INSERT INTO playlist_songs (playlist_id, song_filename) VALUES (%s, %s)",
            (playlist_id, filename)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Canción añadida a la playlist"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()