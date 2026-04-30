from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.auth_service import validate_user  # Función que valida usuario y contraseña
from database.db import get_user_role, get_user_ban, get_db_connection  # Funciones de BD
from werkzeug.security import generate_password_hash  # Para cifrar contraseñas
from datetime import datetime  # Para manejar fechas (baneo)

# Blueprint de autenticación (login, registro, logout)
auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN
# =========================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    # Si se envía el formulario (POST)
    if request.method == 'POST':

        # Obtiene datos del formulario
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Valida usuario (contraseña + existencia)
        if validate_user(username, password):

            # Comprueba si el usuario está baneado
            banned_until = get_user_ban(username)

            # Si está baneado y aún no ha pasado el tiempo
            if banned_until and banned_until > datetime.now():
                return render_template(
                    "login.html",
                    error=f"Usuario baneado hasta {banned_until}"
                )

            # Guarda datos en la sesión
            session['username'] = username
            session['user_id'] = username  # Aquí usas username como ID
            session['role'] = get_user_role(username)  # Guarda el rol

            # Redirige a la página principal de música
            return redirect(url_for('music.index'))

        # Si las credenciales son incorrectas
        return render_template("login.html", error="Credenciales incorrectas")

    # Si es GET → muestra el formulario
    return render_template("login.html")


# =========================
# REGISTRO (POST - API)
# =========================
@auth_bp.route("/register", methods=["POST"])
def register():

    # Obtiene datos JSON (no formulario)
    data = request.get_json()
    username = data.get("username", "").lower()
    password = data.get("password", "")

    # Validación básica
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Todos los campos son obligatorios"
        }), 400

    # Cifra la contraseña antes de guardarla
    hashed_password = generate_password_hash(password)

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Inserta el nuevo usuario en la BD
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Usuario registrado correctamente"
        })

    except Exception as e:
        # Si el usuario ya existe (error típico de MySQL)
        if "Duplicate entry" in str(e):
            return jsonify({
                "success": False,
                "error": "El usuario ya existe"
            }), 409

        # Otro error inesperado
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        # Cierra conexión siempre
        cursor.close()
        conn.close()


# =========================
# REGISTRO (GET)
# =========================
@auth_bp.route("/register", methods=["GET"])
def register_get():
    # Si alguien intenta acceder a /register desde navegador → redirige a login
    return redirect(url_for("auth.login"))


# =========================
# LOGOUT
# =========================
@auth_bp.route('/logout')
def logout():

    # Elimina datos de sesión (logout)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)

    # Redirige al login
    return redirect(url_for('auth.login'))