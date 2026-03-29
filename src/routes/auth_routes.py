from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.auth_service import validate_user
from database.db import get_user_role, get_user_ban, get_db_connection
from werkzeug.security import generate_password_hash
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        if validate_user(username, password):
            banned_until = get_user_ban(username)
            if banned_until and banned_until > datetime.now():
                return render_template("login.html", error=f"Usuario baneado hasta {banned_until}")

            session['username'] = username
            session['user_id'] = username
            session['role'] = get_user_role(username)

            return redirect(url_for('music.index'))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").lower()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "error": "Todos los campos son obligatorios"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Usuario registrado correctamente"})
    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"success": False, "error": "El usuario ya existe"}), 409
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/register", methods=["GET"])
def register_get():
    # Redirige a login si se intenta acceder vía GET
    return redirect(url_for("auth.login"))


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('auth.login'))