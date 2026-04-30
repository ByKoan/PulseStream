import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from services.music_service import get_user_folder
from utils.file_utils import allowed_file
from database.db import get_db_connection

upload_bp = Blueprint(
    "upload",
    __name__,
    template_folder="../templates"
)

# Decorador para proteger rutas que requieren login
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si no hay usuario en sesión, redirigimos al login
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():

    # Obtenemos el usuario actual desde la sesión
    username = session["user_id"]

    # Obtenemos la carpeta específica del usuario
    user_folder = get_user_folder(username)

    # Aseguramos que la carpeta exista
    os.makedirs(user_folder, exist_ok=True)

    # Si el método es POST, significa que se están subiendo archivos
    if request.method == "POST":

        # Comprobamos que la petición contiene archivos
        if "file" not in request.files:
            flash("No se envió ningún archivo", "error")
            return redirect(request.url)

        # Obtenemos la lista de archivos (permite múltiples uploads)
        files = request.files.getlist("file")

        # Si no hay archivos seleccionados
        if not files:
            flash("No seleccionaste ningún archivo", "error")
            return redirect(request.url)

        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        uploaded = False  # Bandera para saber si se subió algo correctamente

        # Iteramos sobre todos los archivos recibidos
        for file in files:

            # Ignorar archivos sin nombre
            if file.filename == "":
                continue

            # Validar extensión permitida
            if not allowed_file(file.filename):
                flash(f"Formato no permitido: {file.filename}", "error")
                continue

            # Sanitizamos el nombre del archivo para evitar problemas de seguridad
            filename = secure_filename(file.filename)

            # Construimos la ruta final del archivo
            file_path = os.path.join(user_folder, filename)

            try:
                # Guardamos el archivo en el sistema
                file.save(file_path)

                # Insertamos la canción en la base de datos
                cursor.execute(
                    """
                    INSERT INTO songs (title, filename, uploaded_by, plays)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (filename, filename, username, 0)
                )

                # Actualizamos el contador de canciones del usuario
                cursor.execute(
                    """
                    UPDATE users
                    SET total_songs = total_songs + 1
                    WHERE username = %s
                    """,
                    (username,)
                )

                uploaded = True  # Marcamos que al menos una canción se subió

            except Exception as e:
                # Si algo falla, revertimos cambios y mostramos error
                conn.rollback()
                flash(f"Error subiendo {filename}: {str(e)}", "error")

        # Confirmamos todos los cambios en la base de datos
        conn.commit()
        cursor.close()
        conn.close()

        # Mensajes finales según resultado
        if uploaded:
            flash("Canciones subidas correctamente", "success")
            return redirect(url_for("music.index"))

        flash("No se subió ninguna canción", "error")
        return redirect(request.url)

    # Si es GET, mostramos la página de subida
    return render_template("upload.html")