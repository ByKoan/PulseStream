import os  # Para trabajar con rutas y archivos del sistema
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, jsonify

from services.music_service import get_user_folder  # Obtiene la carpeta del usuario
from utils.file_utils import allowed_file  # Valida tipos de archivo permitidos
from database.db import get_db_connection  # Conexión a la base de datos

# Blueprint de música (gestión de canciones)
music_bp = Blueprint("music", __name__)


# =========================
# Página principal
# =========================
@music_bp.route("/")
def index():

    # Verifica si el usuario está logueado
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtiene las canciones del usuario
    cursor.execute(
        "SELECT filename FROM songs WHERE uploaded_by = %s",
        (username,)
    )
    songs = [row["filename"] for row in cursor.fetchall()]

    # Obtiene las playlists del usuario
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
        current_song="",  # No hay canción seleccionada al inicio
        playlists=playlists
    )


# =========================
# Reproducir canción
# =========================
@music_bp.route("/play/<filename>")
def play(filename):

    # Verifica sesión
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    # Obtiene la ruta del archivo del usuario
    user_folder = get_user_folder(username)
    file_path = os.path.join(user_folder, filename)

    # Comprueba que el archivo existe y es válido
    if os.path.isfile(file_path) and allowed_file(filename):

        # Conecta a la BD para actualizar reproducciones
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Incrementa el contador de reproducciones
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
            # Si falla, muestra error en consola
            print(f"Error al actualizar plays: {e}")

        finally:
            cursor.close()
            conn.close()

        # Envía el archivo al navegador para reproducirlo
        return send_file(file_path)

    # Si no existe o no es válido
    return "Archivo no encontrado", 404


# =========================
# Eliminar canción
# =========================
@music_bp.route("/delete_song", methods=["POST"])
def delete_song():

    # Verifica sesión
    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 403

    username = session["user_id"]

    # Obtiene datos JSON
    data = request.get_json()
    filename = data.get("filename")

    # Valida archivo
    if not filename or not allowed_file(filename):
        return jsonify({"error": "Archivo no válido"}), 400

    # Ruta del archivo en disco
    filepath = os.path.join(get_user_folder(username), filename)

    # Conexión a BD
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Elimina la canción de la base de datos
        cursor.execute(
            "DELETE FROM songs WHERE filename = %s AND uploaded_by = %s",
            (filename, username)
        )

        conn.commit()

    except Exception as e:
        # Error al borrar en BD
        return jsonify({"error": f"No se pudo borrar de la BD: {e}"}), 500

    finally:
        cursor.close()
        conn.close()

    # Elimina el archivo del disco si existe
    if os.path.exists(filepath):

        try:
            os.remove(filepath)

        except Exception as e:
            return jsonify({"error": f"No se pudo borrar del disco: {e}"}), 500

    # Respuesta exitosa
    return jsonify({"success": True})