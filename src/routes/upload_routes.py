import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

from services.music_service import get_user_folder
from utils.file_utils import allowed_file

upload_bp = Blueprint("upload", __name__, template_folder="../templates")


@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_folder = get_user_folder(session['user_id'])

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No se envió ningún archivo", 400

        files = request.files.getlist('file')

        for file in files:
            if file.filename == '':
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))

        return redirect(url_for('music.index'))

    return render_template("upload.html")