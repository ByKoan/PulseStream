# =============================================================================
# remove_from_playlist.py — Eliminar canciones de una playlist
# Usado en: playlist_player.js (botón eliminar en la vista de playlist)
#
# Responsabilidades:
#   - Verificar que el usuario esté autenticado
#   - Validar que la playlist pertenece al usuario actual
#   - Buscar el ID de la canción a partir de su nombre de archivo
#   - Eliminar la relación canción-playlist de la BD (no borra el archivo)
#
# Endpoints que expone:
#   POST /remove_from_playlist  → desvincula una canción de una playlist
# =============================================================================

from flask import Blueprint, request, jsonify, session  # Herramientas de Flask para rutas, datos y sesión
from database.db import get_db_connection               # Conexión a la base de datos

# Blueprint (módulo de rutas) para eliminar canciones de playlists
remove_playlist_bp = Blueprint("remove_playlist", __name__)


# ===============================
# ELIMINAR CANCIÓN DE PLAYLIST
# Recibe filename + playlist_id, verifica propiedad y borra la fila
# en playlist_songs. No elimina el archivo ni la canción de la BD.
# ===============================
@remove_playlist_bp.route("/remove_from_playlist", methods=["POST"])
def remove_from_playlist():

    # Comprobamos que el usuario ha iniciado sesión
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    # Obtenemos los datos enviados en la petición (JSON)
    data = request.get_json()
    filename    = data.get("filename")      # Nombre del archivo a desvinvular
    playlist_id = data.get("playlist_id")   # ID de la playlist de origen

    # Validamos que se hayan enviado todos los datos necesarios
    if not filename or not playlist_id:
        return jsonify({"success": False, "error": "Faltan datos"}), 400

    # Conexión a la base de datos
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

        # Si no existe o no es del usuario → error
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        # ===============================
        # BUSCAR ID DE LA CANCIÓN
        # Necesitamos el ID numérico para borrar en playlist_songs
        # ===============================
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s",
            (filename,)
        )
        song = cursor.fetchone()

        # Si no existe la canción → error
        if not song:
            return jsonify({"success": False, "error": "Canción no encontrada"}), 404

        song_id = song["id"]

        # ===============================
        # ELIMINAR RELACIÓN CANCIÓN-PLAYLIST
        # Solo borra el vínculo, no la canción en sí
        # ===============================
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
        # Cierra cursor y conexión SIEMPRE (haya error o no)
        cursor.close()
        conn.close()