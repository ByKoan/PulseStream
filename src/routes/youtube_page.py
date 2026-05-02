from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db import get_db_connection
import os
import yt_dlp
from yt_dlp import YoutubeDL

youtube_bp = Blueprint("youtube", __name__, template_folder="../templates")

# Carpeta base donde se guardará la música descargada
BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")


# Función auxiliar para proteger páginas (redirige si no hay sesión)
def login_required_page():
    if "username" not in session:
        return redirect(url_for("auth.login"))
    return None


@youtube_bp.route("/youtube_page")
def youtube_page():
    # Protegemos la página del buscador de YouTube
    redirect_login = login_required_page()
    if redirect_login:
        return redirect_login

    # Renderizamos la página principal de YouTube
    return render_template("youtube.html")


@youtube_bp.route("/youtube_search", methods=["POST"])
def youtube_search():

    # Verificamos que el usuario esté logueado
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    # Obtenemos el texto de búsqueda enviado por el frontend
    data = request.get_json()
    query = data.get("query")

    # Validamos que la query no esté vacía
    if not query:
        return jsonify({"success": False, "error": "Query vacía"}), 400

    try:
        # Configuración de yt-dlp para búsqueda rápida sin descargar
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True
        }

        results = []

        # Realizamos búsqueda en YouTube (ytsearch10 = top 10 resultados)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search = ydl.extract_info(f"ytsearch10:{query}", download=False)

            # Procesamos cada resultado
            for entry in search["entries"]:
                video_id = entry.get("id")
                title = entry.get("title")

                # Si no hay ID válido, ignoramos el resultado
                if not video_id:
                    continue

                # Guardamos título y URL completa del video
                results.append({
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

        # Devolvemos resultados al frontend
        return jsonify({"success": True, "results": results})

    except Exception as e:
        # Manejo de errores generales
        return jsonify({"success": False, "error": str(e)})


@youtube_bp.route("/youtube_audio", methods=["POST"])
def youtube_audio():

    # Verificación de sesión
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    # Obtenemos URL del video
    data = request.get_json()
    url = data.get("url")

    # Validamos entrada
    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:
        # Configuración para extraer solo audio
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True
        }

        # Extraemos información del video sin descargarlo
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        # Respondemos con el enlace directo del audio
        return jsonify({
            "success": True,
            "audio": audio_url,
            "title": info.get("title", "Unknown")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
    
@youtube_bp.route("/youtube_video", methods=["POST"])
def youtube_video():

    # Si el usuario no está logueado, se bloquea el acceso
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    url = data.get("url")

    # Validamos que la URL exista
    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:
        # - best[ext=mp4]/best → prioriza mp4 (mejor compatibilidad en navegadores)
        # - quiet → sin logs en consola
        # - noplaylist → evita procesar listas completas
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True
        }

        # download=False → solo obtiene metadata y URLs de streaming
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Recorremos todos los formatos disponibles
        stream_url = None

        for f in info.get("formats", []):
            if (
                f.get("url")                 # tiene URL válida
                and f.get("vcodec") != "none"  # contiene video
                and f.get("acodec") != "none"  # contiene audio
            ):
                stream_url = f["url"]
                break  # usamos el primero válido

        # Si no encontramos formato combinado, usamos el general
        if not stream_url:
            stream_url = info.get("url")

        # Respuesta al frontend
        return jsonify({
            "success": True,
            "stream": stream_url,           # URL directa del stream
            "title": info.get("title"),     # título del video
            "thumbnail": info.get("thumbnail")  # miniatura
        })

    except Exception as e:
        # Manejo de errores
        return jsonify({"success": False, "error": str(e)})


@youtube_bp.route("/youtube_download", methods=["POST"])
def youtube_download():

    # Verificación de sesión
    if "username" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    # Obtenemos URL del video
    data = request.get_json()
    url = data.get("url")

    # Validamos que exista URL
    if not url:
        return jsonify({"success": False, "error": "No se proporcionó URL"}), 400

    try:
        username = session["username"]  # usuario actual

        # Creamos carpeta del usuario si no existe
        user_folder = os.path.join(BASE_MUSIC_FOLDER, username)
        os.makedirs(user_folder, exist_ok=True)

        # Configuración de descarga de audio en MP3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(user_folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        # Descargamos el audio desde YouTube
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Ajustamos extensión final a mp3
        base = os.path.splitext(filename)[0]
        filename = base + ".mp3"

        # Guardamos información en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            title = info.get("title", "Unknown")

            # Insertamos canción en tabla songs
            cursor.execute("""
                INSERT IGNORE INTO songs (title, filename, uploaded_by)
                VALUES (%s, %s, %s)
            """, (title, os.path.basename(filename), username))

            # Incrementamos contador de canciones del usuario
            cursor.execute("""
                UPDATE users
                SET total_songs = total_songs + 1
                WHERE username = %s
            """, (username,))

            conn.commit()

        finally:
            # Cerramos conexión a base de datos
            cursor.close()
            conn.close()

        # Respuesta exitosa con nombre del archivo
        return jsonify({"success": True, "filename": os.path.basename(filename)})

    except Exception as e:
        # Manejo de errores generales
        return jsonify({"success": False, "error": str(e)})