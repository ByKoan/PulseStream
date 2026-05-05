# =============================================================================
# add_to_playlist.py — Añadir canciones a una playlist
# Usado en: player.js (dropdown por canción en la biblioteca)
#
# Responsabilidades:
#   - Verificar que el usuario esté autenticado
#   - Validar que la playlist pertenece al usuario actual
#   - Validar que la canción pertenece al usuario actual
#   - Evitar duplicados (misma canción en la misma playlist)
#   - Insertar la relación canción-playlist en la BD
#
# Endpoints que expone:
#   POST /add_to_playlist  → añade una canción a una playlist del usuario
# =============================================================================

from flask import Blueprint, request, jsonify, session  # Herramientas de Flask para rutas, datos y sesión
from database.db import get_db_connection               # Conexión a la base de datos

# Blueprint (módulo de rutas) para añadir canciones a playlists
add_playlist_bp = Blueprint("add_playlist", __name__)


# ===============================
# AÑADIR CANCIÓN A PLAYLIST
# Recibe filename + playlist_id, verifica pertenencia de ambos al usuario
# y los vincula en playlist_songs si no estaban ya juntos.
# ===============================
@add_playlist_bp.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():

    # Verifica si el usuario ha iniciado sesión
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    # Obtiene los datos enviados en formato JSON
    data = request.get_json()
    filename    = data.get("filename")        # Nombre del archivo de la canción
    playlist_id = data.get("playlist_id")     # ID de la playlist destino

    # Comprueba que se han enviado todos los datos necesarios
    if not filename or not playlist_id:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    # Conecta con la base de datos
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ===============================
        # VERIFICAR PROPIEDAD DE LA PLAYLIST
        # ===============================
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )
        playlist = cursor.fetchone()

        # Si no existe o no es del usuario → error
        if not playlist:
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        # ===============================
        # VERIFICAR PROPIEDAD DE LA CANCIÓN
        # ===============================
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, session["user_id"])
        )
        song = cursor.fetchone()

        # Si la canción no existe o pertenece a otro usuario → error
        if not song:
            return jsonify({"success": False, "error": "Canción no encontrada"}), 404

        song_id = song["id"]

        # ===============================
        # VERIFICAR DUPLICADOS
        # Evita insertar la misma canción dos veces en la misma playlist
        # ===============================
        cursor.execute(
            "SELECT id FROM playlist_songs WHERE playlist_id=%s AND song_id=%s",
            (playlist_id, song_id)
        )

        if cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "La canción ya está en la playlist"
            }), 409

        # ===============================
        # INSERTAR RELACIÓN CANCIÓN-PLAYLIST
        # ===============================
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
        # Error inesperado → devuelve error 500
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        # Cierra cursor y conexión SIEMPRE (haya error o no)
        cursor.close()
        conn.close()