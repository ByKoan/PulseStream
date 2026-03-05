import os
from flask import Flask, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import time

app = Flask(__name__)
app.secret_key = os.urandom(512)  # Clave secreta para manejar sesiones

BASE_MUSIC_FOLDER = r"C:\Users\Koan0xFF\Desktop\MusicCloudServer_TFG\src\music" # La ruta hacia tu carpeta de la musica
ALLOWED_EXTENSIONS = {'mp3', 'm4a', 'wav'}

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",          # nombre del servicio docker
        user="root",
        password="toor",
        database="musicdb"
    )

def wait_for_db():
    while True:
        try:
            conn = get_db_connection()
            conn.close()
            print("MySQL conectado ✅")
            break
        except Exception as e:
            print("Esperando MySQL...", e)
            time.sleep(2)

def create_user_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def validate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return True
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No se envió ningún archivo", 400
        
        files = request.files.getlist('file')
        if not files:
            return "No se seleccionaron archivos", 400

        for file in files:
            if file.filename == '': 
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))

        return redirect(url_for('index'))
    return "Sube tus archivos aquí."

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    os.makedirs(user_folder, exist_ok=True)

    songs = [f for f in os.listdir(user_folder) if allowed_file(f)]

    query = request.args.get('search', '').strip().lower()
    if query:
        songs = [song for song in songs if query in song.lower()]

    current_song = songs[0] if songs else "No hay canciones"

    return render_template("index.html",songs=songs,current_song=current_song)

@app.route('/play/<filename>')
def play(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    file_path = os.path.join(user_folder, filename)
    if os.path.isfile(file_path) and allowed_file(filename):
        return send_file(file_path)
    return "Archivo no encontrado", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower() 
        password = request.form.get('password', '').strip()

        if validate_user(username, password):
            session['user_id'] = username
            return redirect(url_for('index'))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    wait_for_db()
    create_user_db()
    app.run(host='0.0.0.0', port=5000)
