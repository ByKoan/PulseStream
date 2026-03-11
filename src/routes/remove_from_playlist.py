from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection

remove_playlist_bp = Blueprint("remove_playlist", __name__)

@remove_playlist_bp.route("/remove_from_playlist", methods=["POST"])
def remove_from_playlist():

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
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )

        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404


        # Obtener el song_id usando el filename
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s",
            (filename,)
        )

        song = cursor.fetchone()

        if not song:
            return jsonify({"success": False, "error": "Canción no encontrada"}), 404

        song_id = song["id"]


        # Eliminar de playlist
        cursor.execute(
            "DELETE FROM playlist_songs WHERE playlist_id=%s AND song_id=%s",
            (playlist_id, song_id)
        )

        conn.commit()

        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()