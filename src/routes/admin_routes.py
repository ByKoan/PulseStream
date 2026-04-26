import functools  # Permite crear decoradores
import psutil  # Para obtener información del sistema (CPU, RAM, disco, red)
from datetime import datetime, timedelta  # Manejo de fechas y tiempos
from werkzeug.security import generate_password_hash  # Para cifrar contraseñas

from flask import Blueprint, session, redirect, url_for, render_template, request, flash, jsonify
from database.db import get_user_role, get_db_connection  # Funciones de base de datos
from resources.manage_database_script import add_user  # Función para crear usuarios
from mysql.connector import IntegrityError  # Error cuando hay duplicados en la BD

# =========================
# Crear blueprint de admin
# =========================
admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="../templates",
    url_prefix="/admin"   # Todas las rutas empiezan por /admin
)


# =========================
# Decorador admin (control de acceso)
# =========================
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):

        # Si no hay sesión → no está logueado
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        # Obtiene el rol del usuario
        role = get_user_role(session["user_id"])

        # Si no es admin → acceso denegado
        if role != "admin":
            flash("No tienes permisos de administrador", "error")
            return redirect(url_for("music.index"))

        # Si todo está bien → ejecuta la función original
        return f(*args, **kwargs)

    return decorated_function


# =========================
# Panel de administración
# =========================
@admin_bp.route("/", methods=["GET", "POST"])
@admin_required
def admin_panel():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # Crear usuario (formulario)
    # =========================
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")  # Por defecto "user"

        if username and password:
            try:
                add_user(username, password, role)  # Inserta en la BD
                flash(f"Usuario {username} creado con rol {role}", "success")
            except IntegrityError:
                # Error si el usuario ya existe
                flash("El usuario ya existe", "error")

        return redirect(url_for("admin.admin_panel"))

    # =========================
    # Buscador de usuarios
    # =========================
    search = request.args.get("search", "")

    if search:
        # Busca usuarios por nombre (LIKE)
        cursor.execute(
            "SELECT id, username, role, banned_until FROM users WHERE username LIKE %s",
            ("%" + search + "%",)
        )
    else:
        # Si no hay búsqueda → muestra todos
        cursor.execute("SELECT id, username, role, banned_until FROM users")

    users = cursor.fetchall()

    # =========================
    # Estadísticas del servidor (BD)
    # =========================

    # Total usuarios
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]

    # Total canciones
    cursor.execute("SELECT COUNT(*) AS total_songs FROM songs")
    total_songs = cursor.fetchone()["total_songs"]

    # Total reproducciones
    cursor.execute("SELECT SUM(plays) AS total_plays FROM songs")
    result = cursor.fetchone()
    total_plays = result["total_plays"] or 0  # Si es None → 0

    # Canción más reproducida
    cursor.execute("""
    SELECT title, plays
    FROM songs
    ORDER BY plays DESC
    LIMIT 1
    """)
    top_song = cursor.fetchone()

    # Usuario con más canciones
    cursor.execute("""
    SELECT username, total_songs AS total
    FROM users
    ORDER BY total_songs DESC
    LIMIT 1
    """)
    top_user = cursor.fetchone()

    # Diccionario con stats
    server_stats = {
        "total_users": total_users,
        "total_songs": total_songs,
        "total_plays": total_plays,
        "top_song": top_song,
        "top_user": top_user
    }

    # Cierra conexión BD
    cursor.close()
    conn.close()

    # =========================
    # Recursos del sistema (CPU, RAM, etc.)
    # =========================
    cpu = psutil.cpu_percent(interval=1)  # % CPU
    ram = psutil.virtual_memory()  # Info RAM
    disk = psutil.disk_usage("/")  # Disco
    net = psutil.net_io_counters()  # Red

    stats = {
        "cpu": cpu,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / (1024**3), 2),  # GB usados
        "ram_total": round(ram.total / (1024**3), 2), # GB totales
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / (1024**3), 2),
        "disk_total": round(disk.total / (1024**3), 2),
        "net_sent": net.bytes_sent,
        "net_recv": net.bytes_recv
    }

    # Renderiza la plantilla HTML con todos los datos
    return render_template(
        "admin_panel.html",
        users=users,
        search=search,
        stats=stats,
        server_stats=server_stats
    )


# =========================
# Cambiar rol de usuario
# =========================
@admin_bp.route("/change_role/<username>", methods=["POST"])
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
@admin_bp.route("/delete/<int:user_id>", methods=["POST"])
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
# Banear usuario temporalmente
# =========================
@admin_bp.route("/ban_user", methods=["POST"])
@admin_required
def ban_user():
    user_id = request.form.get("user_id")
    hours = request.form.get("hours")

    # Validación básica
    if not user_id or not hours:
        flash("Datos inválidos")
        return redirect(url_for("admin.admin_panel"))

    try:
        hours = int(hours)
    except ValueError:
        flash("Horas inválidas")
        return redirect(url_for("admin.admin_panel"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Añade horas al tiempo actual
        cursor.execute(
            "UPDATE users SET banned_until = DATE_ADD(NOW(), INTERVAL %s HOUR) WHERE id = %s",
            (hours, user_id)
        )
        conn.commit()
        flash(f"Usuario {user_id} baneado por {hours} horas")

    except Exception as e:
        flash(f"No se pudo banear al usuario: {e}")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("admin.admin_panel"))


# =========================
# Quitar ban (desbanear)
# =========================
@admin_bp.route("/unban_user", methods=["POST"])
@admin_required
def unban_user():

    username = request.form.get("username")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Elimina el tiempo de baneo
    cursor.execute(
        "UPDATE users SET banned_until = NULL WHERE username = %s",
        (username,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin.admin_panel"))


# =========================
# Cambiar contraseña
# =========================
@admin_bp.route("/change_password/<username>", methods=["POST"])
@admin_required
def change_password(username):

    new_password = request.form.get("password")

    # Validación
    if not new_password:
        flash("Contraseña inválida", "error")
        return redirect(url_for("admin.admin_panel"))

    # Cifra la nueva contraseña
    hashed_password = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE users SET password=%s WHERE username=%s",
            (hashed_password, username)
        )

    finally:
        conn.commit()
        cursor.close()
        conn.close()

    flash(f"Contraseña de {username} actualizada", "success")

    return redirect(url_for("admin.admin_panel"))


# =========================
# API para stats en tiempo real
# =========================
@admin_bp.route("/system_stats")
@admin_required
def system_stats():

    # Obtiene datos del sistema en tiempo real
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    # Devuelve los datos en formato JSON (para AJAX o frontend dinámico)
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