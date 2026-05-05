# =============================================================================
# upload_routes.py — Subida de canciones a la biblioteca del usuario
# Usado en: upload.html, upload.js
#
# Responsabilidades:
#   - Proteger la ruta con login obligatorio (decorador login_required)
#   - Aceptar uno o varios archivos de audio en una misma petición
#   - Validar extensiones permitidas antes de guardar
#   - Sanitizar nombres de archivo para evitar problemas de seguridad
#   - Guardar el archivo en la carpeta del usuario en disco
#   - Insertar la canción en la BD y actualizar el contador del usuario
#
# Endpoints que expone:
#   GET  /upload  → muestra el formulario de subida
#   POST /upload  → procesa y guarda los archivos recibidos
# =============================================================================

import os  # Manejo de rutas y carpetas del sistema de archivos
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename      # Sanitiza nombres de archivo
from services.music_service import get_user_folder  # Devuelve la carpeta del usuario
from utils.file_utils import allowed_file           # Valida extensiones permitidas
from database.db import get_db_connection           # Conexión a la base de datos

# Blueprint de subida de archivos
upload_bp = Blueprint(
    "upload",
    __name__,
    template_folder="../templates"
)


# ===============================
# DECORADOR: LOGIN REQUERIDO
# Redirige al login si el usuario no tiene sesión activa.
# Se aplica a todas las rutas de este blueprint que lo necesiten.
# ===============================
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si no hay usuario en sesión → redirige al login
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ===============================
# SUBIDA DE ARCHIVO(S)
# GET  → muestra el formulario de subida
# POST → procesa los archivos recibidos, los guarda en disco y en la BD
# Acepta múltiples archivos en una sola petición.
# ===============================
@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():

    # Obtenemos el usuario actual desde la sesión
    username = session["user_id"]

    # Obtenemos la carpeta específica del usuario en disco
    user_folder = get_user_folder(username)

    # Creamos la carpeta si no existe (exist_ok evita error si ya existe)
    os.makedirs(user_folder, exist_ok=True)

    # Si el método es POST → procesamos los archivos enviados
    if request.method == "POST":

        # Comprobamos que la petición contiene el campo "file"
        if "file" not in request.files:
            flash("No se envió ningún archivo", "error")
            return redirect(request.url)

        # Obtenemos la lista de archivos (permite múltiples uploads a la vez)
        files = request.files.getlist("file")

        # Si la lista está vacía → error
        if not files:
            flash("No seleccionaste ningún archivo", "error")
            return redirect(request.url)

        # Conexión a la base de datos
        conn   = get_db_connection()
        cursor = conn.cursor()

        uploaded = False  # Bandera: se pone a True si al menos un archivo se sube bien

        # ===============================
        # PROCESAR CADA ARCHIVO
        # ===============================
        for file in files:

            # Ignorar entradas vacías (usuario no seleccionó nada)
            if file.filename == "":
                continue

            # Validar que la extensión esté en la lista permitida
            if not allowed_file(file.filename):
                flash(f"Formato no permitido: {file.filename}", "error")
                continue

            # Sanitizamos el nombre para evitar path traversal y caracteres peligrosos
            filename  = secure_filename(file.filename)
            file_path = os.path.join(user_folder, filename)  # Ruta completa en disco

            try:
                # Guarda el archivo en disco
                file.save(file_path)

                # Inserta la canción en la base de datos
                cursor.execute(
                    """
                    INSERT INTO songs (title, filename, uploaded_by, plays)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (filename, filename, username, 0)   # plays empieza en 0
                )

                # Incrementa el contador de canciones del usuario
                cursor.execute(
                    """
                    UPDATE users
                    SET total_songs = total_songs + 1
                    WHERE username = %s
                    """,
                    (username,)
                )

                uploaded = True  # Al menos una canción subida correctamente

            except Exception as e:
                # Algo falló → revertimos cambios de este archivo y mostramos error
                conn.rollback()
                flash(f"Error subiendo {filename}: {str(e)}", "error")

        # Confirmamos todos los cambios en la base de datos
        conn.commit()
        cursor.close()
        conn.close()

        # ===============================
        # MENSAJES FINALES
        # ===============================
        if uploaded:
            flash("Canciones subidas correctamente", "success")
            return redirect(url_for("music.index"))

        flash("No se subió ninguna canción", "error")
        return redirect(request.url)

    # Si es GET → mostramos la página de subida
    return render_template("upload.html")