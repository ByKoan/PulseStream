from flask import Blueprint, render_template, request, redirect, url_for, session
from services.auth_service import validate_user
from database.db import get_user_role

auth_bp = Blueprint("auth", __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        if validate_user(username, password):
            # Guardamos username en sesión para usarlo al subir canciones
            session['user_id'] = username 
            session['username'] = username 
            session['role'] = get_user_role(username)
            return redirect(url_for('music.index'))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@auth_bp.route('/logout')
def logout():

    session.pop('user_id', None)
    session.pop('username', None) 
    session.pop('role', None)
    return redirect(url_for('auth.login'))