import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from services.music_service import get_user_folder
from utils.file_utils import allowed_file
from database.db import get_db_connection


# =========================
# Blueprint
# =========================
upload_bp = Blueprint(
    "upload",
    __name__,
    template_folder="../templates"
)


# =========================
# Upload de canciones
# =========================
@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():

    # Verificar sesión
    if 'user_id' not in session or 'username' not in session:
        flash("Debes iniciar sesión para subir canciones", "error")
        return redirect(url_for('auth.login'))

    username = session['username']  # username del usuario logueado
    user_folder = get_user_folder(session['user_id'])

    if request.method == 'POST':

        if 'file' not in request.files:
            flash("No se envió ningún archivo", "error")
            return redirect(url_for('upload.upload_file'))

        files = request.files.getlist('file')

        if not files:
            flash("No seleccionaste ningún archivo", "error")
            return redirect(url_for('upload.upload_file'))

        # Conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        for file in files:
            if file.filename == '':
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                # Guardar archivo en disco
                file_path = os.path.join(user_folder, filename)
                file.save(file_path)

                # Guardar registro en la base de datos
                try:
                    # INSERT canción
                    cursor.execute(
                        "INSERT INTO songs (title, filename, uploaded_by, plays) VALUES (%s, %s, %s, %s)",
                        (filename, filename, username, 0)
                    )

                    # Incrementar total_songs en users
                    cursor.execute(
                        "UPDATE users SET total_songs = total_songs + 1 WHERE username = %s",
                        (username,)
                    )
                except Exception as e:
                    flash(f"No se pudo registrar '{filename}' en la base de datos: {e}", "error")

        conn.commit()
        cursor.close()
        conn.close()

        flash("Archivos subidos correctamente", "success")
        return redirect(url_for('music.index'))

    return render_template("upload.html")