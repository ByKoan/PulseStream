# =============================================================================
# music_routes.py — Página principal, reproducción y eliminación de canciones
# Usado en: index.html, player.js
#
# Responsabilidades:
#   - Mostrar la biblioteca de canciones y playlists del usuario (index)
#   - Servir el stream de audio de una canción e incrementar su contador
#   - Proteger contra path traversal al resolver rutas de archivos
#   - Eliminar una canción de la BD y del disco a petición del usuario
#
# Endpoints que expone:
#   GET  /                        → página principal con canciones y playlists
#   GET  /play/<filename>         → stream de audio (incrementa plays)
#   POST /delete_song             → elimina canción de BD y disco
# =============================================================================

import os  # Manejo de rutas y archivos del sistema
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, jsonify

from services.music_service import get_user_folder  # Devuelve la carpeta del usuario
from utils.file_utils import allowed_file           # Valida extensiones permitidas
from database.db import get_db_connection           # Conexión a la base de datos

# Blueprint de música (gestión de canciones)
music_bp = Blueprint("music", __name__)


# ===============================
# PÁGINA PRINCIPAL (BIBLIOTECA)
# Carga las canciones y playlists del usuario y renderiza index.html.
# Redirige al login si no hay sesión activa.
# ===============================
@music_bp.route("/")
def index():

    # Verifica si el usuario está logueado
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    # Conexión a la base de datos
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtiene los nombres de archivo de todas las canciones del usuario
    cursor.execute(
        "SELECT filename FROM songs WHERE uploaded_by = %s",
        (username,)
    )
    songs = [row["filename"] for row in cursor.fetchall()]

    # Obtiene las playlists del usuario (ID + nombre para el dropdown)
    cursor.execute(
        "SELECT id, name FROM playlists WHERE user_id = %s",
        (username,)
    )
    playlists = cursor.fetchall()

    # Cierra conexión
    cursor.close()
    conn.close()

    # Renderiza la página principal con canciones y playlists
    return render_template(
        "index.html",
        songs=songs,
        current_song="",    # Ninguna canción preseleccionada al cargar
        playlists=playlists
    )


# ===============================
# REPRODUCIR CANCIÓN (STREAMING)
# Sirve el archivo de audio al navegador.
# Protege contra path traversal resolviendo rutas reales.
# Incrementa el contador de reproducciones en la BD.
# conditional=True habilita Range requests (seek en el player HTML5).
# ===============================
@music_bp.route("/play/<path:filename>")
def play(filename):

    # Verifica sesión
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    # Ruta completa del archivo en disco
    user_folder = get_user_folder(username)
    file_path   = os.path.join(user_folder, filename)

    # ===============================
    # PROTECCIÓN CONTRA PATH TRAVERSAL
    # Resuelve symlinks y ".." para asegurarse de que el archivo
    # está realmente dentro de la carpeta del usuario
    # ===============================
    real_file_path  = os.path.realpath(file_path)
    real_user_folder = os.path.realpath(user_folder)
    if not real_file_path.startswith(real_user_folder + os.sep):
        return "Acceso no permitido", 403

    # Comprueba que el archivo existe y tiene extensión permitida
    if os.path.isfile(file_path) and allowed_file(filename):

        # Conexión a BD para actualizar reproducciones
        conn   = get_db_connection()
        cursor = conn.cursor()

        try:
            # Incrementa el contador de reproducciones de la canción
            cursor.execute(
                """
                UPDATE songs
                SET plays = plays + 1
                WHERE filename = %s AND uploaded_by = %s
                """,
                (filename, username)
            )
            conn.commit()

        except Exception as e:
            # Si falla el contador no bloqueamos la reproducción
            print(f"Error al actualizar plays: {e}")

        finally:
            cursor.close()
            conn.close()

        # Sirve el archivo al navegador
        # conditional=True → soporte de Range requests (seek / avance en el audio)
        return send_file(file_path, conditional=True)

    # El archivo no existe o tiene extensión no permitida
    return "Archivo no encontrado", 404


# ===============================
# ELIMINAR CANCIÓN
# Borra la canción de la BD y del disco.
# No afecta a las playlists (las relaciones en playlist_songs se
# eliminan por CASCADE si la BD está configurada para ello).
# ===============================
@music_bp.route("/delete_song", methods=["POST"])
def delete_song():

    # Verifica sesión
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 403

    username = session["user_id"]

    # Obtiene datos JSON de la petición
    data     = request.get_json()
    filename = data.get("filename")

    # Valida que el nombre de archivo es válido y con extensión permitida
    if not filename or not allowed_file(filename):
        return jsonify({"error": "Archivo no válido"}), 400

    # Ruta completa del archivo en disco
    filepath = os.path.join(get_user_folder(username), filename)

    # Conexión a BD
    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        # Elimina la canción de la base de datos
        cursor.execute(
            "DELETE FROM songs WHERE filename = %s AND uploaded_by = %s",
            (filename, username)
        )
        conn.commit()

    except Exception as e:
        # Error al borrar en BD → no intentamos borrar el archivo
        return jsonify({"error": f"No se pudo borrar de la BD: {e}"}), 500

    finally:
        cursor.close()
        conn.close()

    # Elimina el archivo físico del disco si existe
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            return jsonify({"error": f"No se pudo borrar del disco: {e}"}), 500

    # Respuesta exitosa
    return jsonify({"success": True})