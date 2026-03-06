import functools
from flask import Blueprint, session, redirect, url_for, render_template, request, flash
from database.db import get_user_role, get_db_connection
from resources.manage_database_script import add_user, show_users
from mysql.connector import IntegrityError

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

# =========================
# Decorador para proteger rutas de admin
# =========================
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        role = get_user_role(session["user_id"])
        if role != "admin":
            flash("No tienes permisos de administrador", "error")
            return redirect(url_for("music.index"))
        return f(*args, **kwargs)
    return decorated_function


# =========================
# Panel de Admin
# =========================
@admin_bp.route("/admin/", methods=["GET", "POST"])
@admin_required
def admin_panel():
    # Manejo de creación de usuario
    if request.method == "POST" and request.form.get("action") == "create":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")

        if username and password:
            try:
                add_user(username, password, role)
                flash(f"Usuario {username} creado con rol {role}", "success")
            except IntegrityError:
                flash(f"El usuario {username} ya existe.", "error")

        return redirect(url_for("admin.admin_panel"))

    # Mostrar usuarios
    users = show_users(print=lambda *args: None)
    return render_template("admin_panel.html", users=users)


# =========================
# Cambiar rol de usuario
# =========================
@admin_bp.route("/admin/change_role/<username>", methods=["POST"])
@admin_required
def change_role(username):
    new_role = request.form.get("role")
    if new_role not in ["user", "admin"]:
        flash("Rol inválido", "error")
        return redirect(url_for("admin.admin_panel"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET role=%s WHERE username=%s", (new_role, username))
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    flash(f"Rol de {username} cambiado a {new_role}", "success")
    return redirect(url_for("admin.admin_panel"))


# =========================
# Eliminar usuario
# =========================
@admin_bp.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    # Evitar que el admin elimine su propio usuario
    if session.get('user_id') == get_username_by_id(user_id):
        flash("No puedes eliminar tu propio usuario.", "error")
        return redirect(url_for("admin.admin_panel"))

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    finally:
        conn.commit()
        cursor.close()
        conn.close()
    flash("Usuario eliminado correctamente.", "success")
    return redirect(url_for("admin.admin_panel"))


# =========================
# Función auxiliar para obtener username por ID
# =========================
def get_username_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        return user["username"] if user else None
    finally:
        cursor.close()
        conn.close()