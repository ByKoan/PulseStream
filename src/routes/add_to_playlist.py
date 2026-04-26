from flask import Blueprint, request, jsonify, session  # Herramientas de Flask para rutas, datos y sesión
from database.db import get_db_connection  # Conexión a la base de datos

# Se crea un Blueprint (módulo de rutas) llamado "add_playlist"
add_playlist_bp = Blueprint("add_playlist", __name__)

# Define una ruta POST para añadir canciones a una playlist
@add_playlist_bp.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():

    # Verifica si el usuario ha iniciado sesión
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    # Obtiene los datos enviados en formato JSON
    data = request.get_json()
    filename = data.get("filename")        # Nombre del archivo de la canción
    playlist_id = data.get("playlist_id")  # ID de la playlist

    # Comprueba que se han enviado todos los datos necesarios
    if not filename or not playlist_id:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    # Conecta con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Verificar que la playlist pertenece al usuario
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )
        playlist = cursor.fetchone()

        # Si no existe o no es del usuario → error
        if not playlist:
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        # 2. Buscar la canción del usuario
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, session["user_id"])
        )
        song = cursor.fetchone()

        # Si no existe → error
        if not song:
            return jsonify({"success": False, "error": "Canción no encontrada"}), 404

        # Guarda el ID de la canción
        song_id = song["id"]

        # 3. Verificar que la canción no esté ya en la playlist
        cursor.execute(
            "SELECT id FROM playlist_songs WHERE playlist_id=%s AND song_id=%s",
            (playlist_id, song_id)
        )

        # Si ya existe → evita duplicados
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "La canción ya está en la playlist"
            }), 409

        # 4. Insertar la canción en la playlist
        cursor.execute(
            "INSERT INTO playlist_songs (playlist_id, song_id) VALUES (%s, %s)",
            (playlist_id, song_id)
        )

        # Guarda los cambios en la base de datos
        conn.commit()

        # Respuesta exitosa
        return jsonify({
            "success": True,
            "message": "Canción añadida a la playlist"
        })

    except Exception as e:
        # Si ocurre un error inesperado → devuelve error 500
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        # Cierra cursor y conexión SIEMPRE (haya error o no)
        cursor.close()
        conn.close()