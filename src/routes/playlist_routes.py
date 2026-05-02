from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, send_from_directory, abort
from database.db import get_db_connection  # Conexión a la base de datos

import os  # Manejo de archivos y rutas
import yt_dlp  # Descarga contenido de YouTube

from config import Config  # Configuración (ruta base de música)
from utils.file_utils import allowed_file  # Valida extensiones de archivos

# Blueprint para gestionar playlists
playlist_bp = Blueprint("playlist", __name__)


# =========================
# Mostrar playlists
# =========================
@playlist_bp.route("/playlists")
def playlists():

    # Verifica sesión
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtiene todas las playlists del usuario
    cursor.execute(
        "SELECT * FROM playlists WHERE user_id = %s",
        (session["user_id"],)
    )

    playlists = cursor.fetchall()

    cursor.close()
    conn.close()

    # Renderiza la vista con las playlists
    return render_template("playlists.html", playlists=playlists)


# =========================
# Crear playlist
# =========================
@playlist_bp.route("/create_playlist", methods=["POST"])
def create_playlist():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    name = request.form.get("name")

    # Validación básica
    if not name:
        return redirect(url_for("playlist.playlists"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Inserta nueva playlist
    cursor.execute(
        "INSERT INTO playlists (name, user_id) VALUES (%s,%s)",
        (name, session["user_id"])
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("playlist.playlists"))


# =========================
# Ver una playlist concreta
# =========================
@playlist_bp.route("/playlist/<int:playlist_id>")
def view_playlist(playlist_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verifica que la playlist pertenece al usuario
        cursor.execute(
            "SELECT * FROM playlists WHERE id=%s AND user_id=%s", 
            (playlist_id, session['user_id'])
        )
        playlist = cursor.fetchone()

        if not playlist:
            return redirect(url_for("playlist.playlists"))

        # Obtiene canciones de la playlist (JOIN)
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

    # Renderiza la vista de la playlist
    return render_template("playlist_view.html", playlist=playlist, songs=songs)


# =========================
# Eliminar playlist
# =========================
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
        # Verifica propiedad
        cursor.execute("""
            SELECT id FROM playlists 
            WHERE id=%s AND user_id=%s
        """, (playlist_id, session["user_id"]))

        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"})

        # Borra relaciones (canciones en playlist)
        cursor.execute(
            "DELETE FROM playlist_songs WHERE playlist_id=%s",
            (playlist_id,)
        )

        # Borra la playlist
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


# =========================
# Renombrar playlist
# =========================
@playlist_bp.route("/rename_playlist", methods=["POST"])
def rename_playlist():

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
        # Verifica propiedad
        cursor.execute(
            "SELECT id FROM playlists WHERE id=%s AND user_id=%s",
            (playlist_id, session["user_id"])
        )

        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Playlist no encontrada"})

        # Actualiza nombre
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


# =========================
# Importar playlist de YouTube
# =========================
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
        # Obtiene info de la playlist sin descargar
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

        playlist_title = info.get("title", "YouTube Playlist")

        # Extraer el ID de la playlist de YouTube para sincronizaciones futuras
        yt_playlist_id = info.get("id", None)

        # Crea playlist en BD guardando la URL y el ID de YouTube
        cursor.execute("""
            INSERT INTO playlists (name, user_id, youtube_url, youtube_playlist_id, last_synced)
            VALUES (%s, %s, %s, %s, NOW())
        """, (playlist_title, username, youtube_url, yt_playlist_id))

        playlist_id = cursor.lastrowid

        # Carpeta del usuario
        user_music_folder = os.path.join(Config.BASE_MUSIC_FOLDER, username)
        os.makedirs(user_music_folder, exist_ok=True)

        # Opciones de descarga
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

        # Descarga canciones
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(youtube_url, download=True)
            entries = info.get("entries", [])

            for entry in entries:

                if not entry:
                    continue

                title = entry.get("title")
                video_id = entry.get("id") or entry.get("webpage_url_basename")
                filename = f"{title}.mp3"

                # Validación
                if not title or not allowed_file(filename):
                    continue

                # Comprueba si ya existe en BD por video_id o filename
                song = None
                if video_id:
                    cursor.execute("""
                        SELECT id FROM songs
                        WHERE youtube_video_id=%s AND uploaded_by=%s
                    """, (video_id, username))
                    song = cursor.fetchone()

                if not song:
                    cursor.execute("""
                        SELECT id FROM songs
                        WHERE filename=%s AND uploaded_by=%s
                    """, (filename, username))
                    song = cursor.fetchone()

                if song:
                    song_id = song["id"]
                    # Guardar video_id si faltaba
                    if video_id:
                        cursor.execute("""
                            UPDATE songs SET youtube_video_id = %s
                            WHERE id = %s AND (youtube_video_id IS NULL OR youtube_video_id = '')
                        """, (video_id, song_id))
                else:
                    # Inserta nueva canción con youtube_video_id
                    cursor.execute("""
                        INSERT INTO songs (title, filename, uploaded_by, youtube_video_id)
                        VALUES (%s,%s,%s,%s)
                    """, (title, filename, username, video_id))

                    song_id = cursor.lastrowid
                    downloaded += 1

                # Añade canción a la playlist
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
        print("Error importando playlist.")
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# =========================
# Reproducir canción desde playlist
# =========================
@playlist_bp.route("/play/<path:filename>")
def play_song(filename):

    # Verifica sesión
    if "user_id" not in session or "username" not in session:
        abort(401)

    username = session["username"]

    # Ruta del archivo
    user_music_folder = os.path.join(Config.BASE_MUSIC_FOLDER, username)
    file_path = os.path.join(user_music_folder, filename)

    print("PLAY REQUEST:", filename)
    print("PATH:", file_path)

    # Si no existe → error
    if not os.path.exists(file_path):
        print("FILE NOT FOUND")
        abort(404)

    # Envía el archivo
    return send_from_directory(user_music_folder, filename)


# =========================
# Sincronizar playlist con YouTube (aplica cambios)
# =========================
@playlist_bp.route("/sync_youtube_playlist", methods=["POST"])
def sync_youtube_playlist():

    # Verificar sesión de usuario
    if "user_id" not in session:
        return jsonify({"success": False, "error": "No logueado"}), 401

    # Obtener usuario actual
    username = session.get("username")

    # Obtener datos enviados desde frontend
    data = request.get_json()
    playlist_id = data.get("playlist_id")

    # Validación de entrada
    if not playlist_id:
        return jsonify({"success": False, "error": "ID de playlist requerido"}), 400

    # Conexión a base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Obtener playlist del usuario
        cursor.execute("""
            SELECT id, name, youtube_url
            FROM playlists
            WHERE id = %s AND user_id = %s
        """, (playlist_id, session["user_id"]))

        playlist = cursor.fetchone()

        # Validaciones
        if not playlist:
            return jsonify({"success": False, "error": "Playlist no encontrada"}), 404

        if not playlist["youtube_url"]:
            return jsonify({"success": False, "error": "Esta playlist no fue importada de YouTube"}), 400

        # =========================
        # Obtener vídeos de YouTube (sin descargar)
        # =========================
        ydl_opts_flat = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": "in_playlist",  # evita cargar info pesada
            "ignoreerrors": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info = ydl.extract_info(playlist["youtube_url"], download=False)

        # =========================
        # Función recursiva para aplanar playlists (por si hay sublistas)
        # =========================
        def collect_entries(info_dict):
            result = []
            for e in (info_dict.get("entries") or []):
                if not e:
                    continue
                if e.get("entries"):  # si es sublista
                    result.extend(collect_entries(e))
                elif e.get("id"):
                    result.append(e)
            return result

        all_entries = collect_entries(info)

        # =========================
        # Crear mapa: video_id → título
        # =========================
        yt_map = {}
        for e in all_entries:
            vid_id = e.get("id")
            if vid_id:
                yt_map[vid_id] = e.get("title") or vid_id

        yt_vid_ids = set(yt_map.keys())
        print(f"[sync] YouTube tiene {len(yt_vid_ids)} vídeos en la playlist")

        # =========================
        # Obtener canciones locales de la playlist
        # =========================
        cursor.execute("""
            SELECT ps.id AS ps_id, s.id AS song_id,
                   s.title, s.filename,
                   COALESCE(s.youtube_video_id, '') AS yt_vid_id
            FROM playlist_songs ps
            JOIN songs s ON ps.song_id = s.id
            WHERE ps.playlist_id = %s
        """, (playlist_id,))
        local_songs = cursor.fetchall()

        print(f"[sync] Playlist local tiene {len(local_songs)} canciones")

        # =========================
        # BACKFILL: rellenar youtube_video_id si falta
        # =========================
        songs_without_vid = [s for s in local_songs if not s["yt_vid_id"]]

        if songs_without_vid:
            print(f"[sync] Backfill: {len(songs_without_vid)} canciones sin youtube_video_id")

            # Crear mapa título → video_id (normalizado)
            yt_title_to_vid = {
                title.strip().lower(): vid_id
                for vid_id, title in yt_map.items()
            }

            # Intentar emparejar por título
            for song in songs_without_vid:
                title_norm = song["title"].strip().lower()
                matched_vid = yt_title_to_vid.get(title_norm)

                if matched_vid:
                    print(f"[sync] Backfill match: '{song['title']}' -> {matched_vid}")

                    # Actualizar BD
                    cursor.execute("""
                        UPDATE songs SET youtube_video_id = %s WHERE id = %s
                    """, (matched_vid, song["song_id"]))

                    song["yt_vid_id"] = matched_vid

            conn.commit()

        # =========================
        # Comparar local vs YouTube
        # =========================
        local_vid_ids = {s["yt_vid_id"] for s in local_songs if s["yt_vid_id"]}

        # =========================
        # ELIMINAR canciones que ya no están en YouTube
        # =========================
        removed = 0
        for song in local_songs:
            vid_id = song["yt_vid_id"]

            if vid_id and vid_id not in yt_vid_ids:
                print(f"[sync] ELIMINAR '{song['title']}'")

                cursor.execute(
                    "DELETE FROM playlist_songs WHERE id = %s",
                    (song["ps_id"],)
                )
                removed += 1

        # =========================
        # Detectar nuevos vídeos a añadir
        # =========================
        new_vid_ids = yt_vid_ids - local_vid_ids
        print(f"[sync] {len(new_vid_ids)} vídeos nuevos para descargar")

        added = 0

        # Carpeta del usuario
        user_music_folder = os.path.join(Config.BASE_MUSIC_FOLDER, username)
        os.makedirs(user_music_folder, exist_ok=True)

        # =========================
        # DESCARGAR nuevos vídeos
        # =========================
        if new_vid_ids:

            ydl_opts_dl = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(user_music_folder, "%(title)s.%(ext)s"),
                "noplaylist": True,
                "ignoreerrors": True,
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

            for vid_id in new_vid_ids:
                video_url = f"https://www.youtube.com/watch?v={vid_id}"

                try:
                    print(f"[sync] Descargando {vid_id}")

                    # Descargar audio
                    with yt_dlp.YoutubeDL(ydl_opts_dl) as ydl:
                        dl_info = ydl.extract_info(video_url, download=True)

                    if not dl_info:
                        continue

                    title = dl_info.get("title") or yt_map.get(vid_id, vid_id)
                    filename = f"{title}.mp3"

                    # =========================
                    # Verificar si ya existe en BD
                    # =========================
                    cursor.execute("""
                        SELECT id FROM songs
                        WHERE youtube_video_id = %s AND uploaded_by = %s
                    """, (vid_id, username))

                    existing = cursor.fetchone()

                    if not existing:
                        cursor.execute("""
                            SELECT id FROM songs
                            WHERE filename = %s AND uploaded_by = %s
                        """, (filename, username))
                        existing = cursor.fetchone()

                    if existing:
                        # Ya existe -> reutilizar
                        song_id = existing["id"]

                        cursor.execute("""
                            UPDATE songs SET youtube_video_id = %s
                            WHERE id = %s AND (youtube_video_id IS NULL OR youtube_video_id = '')
                        """, (vid_id, song_id))

                    else:
                        # Nueva canción → insertar
                        cursor.execute("""
                            INSERT INTO songs (title, filename, uploaded_by, youtube_video_id)
                            VALUES (%s, %s, %s, %s)
                        """, (title, filename, username, vid_id))

                        song_id = cursor.lastrowid

                    # =========================
                    # Añadir a playlist si no está
                    # =========================
                    cursor.execute("""
                        SELECT id FROM playlist_songs
                        WHERE playlist_id = %s AND song_id = %s
                    """, (playlist_id, song_id))

                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO playlist_songs (playlist_id, song_id)
                            VALUES (%s, %s)
                        """, (playlist_id, song_id))

                        added += 1

                except Exception as e_inner:
                    print(f"[sync] ERROR descargando {vid_id}: {e_inner}")
                    continue

        # =========================
        # Actualizar fecha de sync
        # =========================
        cursor.execute(
            "UPDATE playlists SET last_synced = NOW() WHERE id = %s",
            (playlist_id,)
        )

        conn.commit()

        print(f"[sync] DONE: +{added} añadidas, -{removed} eliminadas")

        return jsonify({
            "success": True,
            "added": added,
            "removed": removed,
            "message": f"Sincronización completada: +{added} añadidas, −{removed} eliminadas"
        })

    except Exception as e:
        # Error general → rollback
        conn.rollback()
        print(f"[sync] EXCEPCIÓN: {e}")
        import traceback; traceback.print_exc()

        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        # Cerrar conexión
        cursor.close()
        conn.close()