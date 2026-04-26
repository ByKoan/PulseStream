from flask import Blueprint, request, jsonify, session
from database.db import get_db_connection

remove_playlist_bp = Blueprint("remove_playlist", __name__)

@remove_playlist_bp.route("/remove_from_playlist", methods=["POST"])
def remove_from_playlist():

    # Comprobamos que el usuario ha iniciado sesión
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401
    
    # Obtenemos los datos enviados en la petición (JSON)
    data = request.get_json()

    filename = data.get("filename")
    playlist_id = data.get("playlist_id")

    # Validamos que se hayan enviado todos los datos necesarios
    if not filename or not playlist_id:
        return jsonify({"success": False, "error": "Faltan datos"}), 400
    
    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # Verificar que la playlist pertenece al usuario actual
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )

        # Si no existe, devolvemos error
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        # Buscar el ID de la canción a partir del nombre del archivo
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s",
            (filename,)
        )

        song = cursor.fetchone()

        # Si no existe la canción, devolvemos error
        if not song:
            return jsonify({"success": False, "error": "Canción no encontrada"}), 404

        song_id = song["id"]

        # Eliminamos la relación canción-playlist
        cursor.execute(
            "DELETE FROM playlist_songs WHERE playlist_id=%s AND song_id=%s",
            (playlist_id, song_id)
        )

        # Guardamos cambios en la base de datos
        conn.commit()

        # Respuesta exitosa
        return jsonify({"success": True})
    
    except Exception as e:
        # Capturamos cualquier error inesperado
        return jsonify({"success": False, "error": str(e)}), 500
    
    finally:
        # Cerramos cursor y conexión siempre
        cursor.close()
        conn.close()