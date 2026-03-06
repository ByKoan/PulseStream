import functools
import psutil

from flask import Blueprint, session, redirect, url_for, render_template, request, flash, jsonify
from database.db import get_user_role, get_db_connection
from resources.manage_database_script import add_user
from mysql.connector import IntegrityError

admin_bp = Blueprint("admin", __name__, template_folder="../templates")


# =========================
# Decorador admin
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
# Panel admin
# =========================
@admin_bp.route("/admin/", methods=["GET", "POST"])
@admin_required
def admin_panel():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # Crear usuario
    # =========================
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")

        if username and password:
            try:
                add_user(username, password, role)
                flash(f"Usuario {username} creado con rol {role}", "success")
            except IntegrityError:
                flash("El usuario ya existe", "error")

        return redirect(url_for("admin.admin_panel"))

    # =========================
    # Buscador
    # =========================
    search = request.args.get("search", "")

    if search:
        cursor.execute(
            "SELECT id, username, role FROM users WHERE username LIKE %s",
            ("%" + search + "%",)
        )
    else:
        cursor.execute("SELECT id, username, role FROM users")

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    # =========================
    # Recursos sistema
    # =========================
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    stats = {
        "cpu": cpu,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / (1024**3), 2),
        "ram_total": round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / (1024**3), 2),
        "disk_total": round(disk.total / (1024**3), 2),
        "net_sent": net.bytes_sent,
        "net_recv": net.bytes_recv
    }

    return render_template(
        "admin_panel.html",
        users=users,
        search=search,
        stats=stats
    )


# =========================
# Cambiar rol
# =========================
@admin_bp.route("/admin/change_role/<username>", methods=["POST"])
@admin_required
def change_role(username):

    new_role = request.form.get("role")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE users SET role=%s WHERE username=%s",
            (new_role, username),
        )

    finally:
        conn.commit()
        cursor.close()
        conn.close()

    flash(f"Rol de {username} actualizado", "success")

    return redirect(url_for("admin.admin_panel"))


# =========================
# Eliminar usuario
# =========================
@admin_bp.route("/admin/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

    finally:
        conn.commit()
        cursor.close()
        conn.close()

    flash("Usuario eliminado correctamente", "success")

    return redirect(url_for("admin.admin_panel"))


# =========================
# API para stats en tiempo real
# =========================
@admin_bp.route("/admin/system_stats")
@admin_required
def system_stats():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return jsonify({
        "cpu": cpu,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / (1024**3), 2),
        "ram_total": round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / (1024**3), 2),
        "disk_total": round(disk.total / (1024**3), 2),
        "net_sent": net.bytes_sent,
        "net_recv": net.bytes_recv
    })