# =============================================================================
# admin_routes.py — Panel de administración
# Usado en: admin_panel.html, admin.js
#
# Responsabilidades:
#   - Proteger todas las rutas con el decorador admin_required
#   - Mostrar el panel principal con lista de usuarios y estadísticas
#   - Crear usuarios desde el formulario del panel
#   - Cambiar el rol de un usuario (user ↔ admin)
#   - Eliminar usuarios
#   - Banear usuarios temporalmente (N horas)
#   - Desbanear usuarios
#   - Cambiar contraseñas de usuarios
#   - Servir estadísticas del sistema en tiempo real (CPU, RAM, disco, red)
#   - Servir estadísticas de BD en tiempo real (polling desde admin.js)
#
# Endpoints que expone:
#   GET/POST /admin/                    → panel principal (crea usuario si POST)
#   POST     /admin/change_role/<user>  → cambia el rol del usuario
#   POST     /admin/delete/<id>         → elimina un usuario
#   POST     /admin/ban_user            → banea un usuario N horas
#   POST     /admin/unban_user          → quita el ban de un usuario
#   POST     /admin/change_password/<u> → cambia la contraseña de un usuario
#   GET      /admin/system_stats        → stats de sistema (JSON, tiempo real)
#   GET      /admin/server_stats_db     → stats de BD (JSON, polling)
# =============================================================================

import functools    # Necesario para crear decoradores que preservan el nombre de la función
import psutil       # Métricas del sistema: CPU, RAM, disco, red
from datetime import datetime, timedelta        # Manejo de fechas y tiempos
from werkzeug.security import generate_password_hash  # Cifrado de contraseñas

from flask import Blueprint, session, redirect, url_for, render_template, request, flash, jsonify
from database.db import get_user_role, get_db_connection    # Funciones de base de datos
from resources.manage_database_script import add_user       # Función para crear usuarios en BD
from mysql.connector import IntegrityError                  # Error de duplicado en BD

# Blueprint de admin — todas las rutas tienen el prefijo /admin
admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="../templates",
    url_prefix="/admin"         # Todas las rutas empiezan por /admin
)


# ===============================
# DECORADOR: ADMIN REQUERIDO
# Bloquea el acceso a cualquier ruta si el usuario no está logueado
# o si su rol no es "admin". Se aplica a todas las rutas del panel.
# ===============================
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):

        # Si no hay sesión → el usuario no está logueado
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        # Consulta el rol actual del usuario en BD
        role = get_user_role(session["user_id"])

        # Si no es admin → acceso denegado, redirige a la biblioteca
        if role != "admin":
            flash("No tienes permisos de administrador", "error")
            return redirect(url_for("music.index"))

        # Rol correcto → ejecuta la función original
        return f(*args, **kwargs)

    return decorated_function


# ===============================
# PANEL PRINCIPAL
# GET  → muestra lista de usuarios + estadísticas del servidor
# POST → crea un usuario nuevo desde el formulario del panel
# ===============================
@admin_bp.route("/", methods=["GET", "POST"])
@admin_required
def admin_panel():

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ===============================
    # CREAR USUARIO (formulario POST)
    # ===============================
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        role     = request.form.get("role", "user")     # "user" por defecto

        if username and password:
            try:
                add_user(username, password, role)       # Inserta en la BD
                flash(f"Usuario {username} creado con rol {role}", "success")
            except IntegrityError:
                # El usuario ya existe en la BD
                flash("El usuario ya existe", "error")

        return redirect(url_for("admin.admin_panel"))

    # ===============================
    # BUSCADOR DE USUARIOS
    # Si hay parámetro ?search= filtra por nombre (LIKE)
    # ===============================
    search = request.args.get("search", "")

    if search:
        # Búsqueda parcial por nombre de usuario
        cursor.execute(
            "SELECT id, username, role, banned_until FROM users WHERE username LIKE %s",
            ("%" + search + "%",)
        )
    else:
        # Sin búsqueda → devuelve todos los usuarios
        cursor.execute("SELECT id, username, role, banned_until FROM users")

    users = cursor.fetchall()

    # ===============================
    # ESTADÍSTICAS DE BD
    # Se renderizan directamente en la plantilla al cargar la página.
    # Para actualizaciones en tiempo real usa /admin/server_stats_db.
    # ===============================

    # Total de usuarios registrados
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]

    # Total de canciones en la plataforma
    cursor.execute("SELECT COUNT(*) AS total_songs FROM songs")
    total_songs = cursor.fetchone()["total_songs"]

    # Total de reproducciones acumuladas
    cursor.execute("SELECT SUM(plays) AS total_plays FROM songs")
    result      = cursor.fetchone()
    total_plays = result["total_plays"] or 0    # None → 0 si no hay canciones

    # Canción más reproducida
    cursor.execute("""
    SELECT title, plays
    FROM songs
    ORDER BY plays DESC
    LIMIT 1
    """)
    top_song = cursor.fetchone()

    # Usuario con más canciones subidas
    cursor.execute("""
    SELECT username, total_songs AS total
    FROM users
    ORDER BY total_songs DESC
    LIMIT 1
    """)
    top_user = cursor.fetchone()

    # Agrupa todas las estadísticas de BD en un diccionario
    server_stats = {
        "total_users": total_users,
        "total_songs": total_songs,
        "total_plays": total_plays,
        "top_song":    top_song,
        "top_user":    top_user
    }

    cursor.close()
    conn.close()

    # ===============================
    # ESTADÍSTICAS DEL SISTEMA (psutil)
    # Se calculan una vez al cargar el panel; para polling usar /system_stats
    # ===============================
    cpu  = psutil.cpu_percent(interval=1)       # % de uso de CPU
    ram  = psutil.virtual_memory()              # Info de RAM
    disk = psutil.disk_usage("/")               # Uso del disco raíz
    net  = psutil.net_io_counters()             # Bytes enviados/recibidos por red

    stats = {
        "cpu":          cpu,
        "ram_percent":  ram.percent,
        "ram_used":     round(ram.used  / (1024**3), 2),   # GB usados
        "ram_total":    round(ram.total / (1024**3), 2),   # GB totales
        "disk_percent": disk.percent,
        "disk_used":    round(disk.used  / (1024**3), 2),
        "disk_total":   round(disk.total / (1024**3), 2),
        "net_sent":     net.bytes_sent,
        "net_recv":     net.bytes_recv
    }

    # Renderiza la plantilla con todos los datos
    return render_template(
        "admin_panel.html",
        users=users,
        search=search,
        stats=stats,
        server_stats=server_stats
    )


# ===============================
# CAMBIAR ROL DE USUARIO
# Actualiza el campo "role" del usuario en la BD.
# ===============================
@admin_bp.route("/change_role/<username>", methods=["POST"])
@admin_required
def change_role(username):

    new_role = request.form.get("role")     # Nuevo rol recibido del formulario

    conn   = get_db_connection()
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


# ===============================
# ELIMINAR USUARIO
# Borra el usuario de la BD por su ID numérico.
# ===============================
@admin_bp.route("/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for("admin.admin_panel"))


# ===============================
# BANEAR USUARIO TEMPORALMENTE
# Establece banned_until = NOW() + N horas en la BD.
# El login comprueba este campo y bloquea el acceso mientras sea futuro.
# ===============================
@admin_bp.route("/ban_user", methods=["POST"])
@admin_required
def ban_user():

    user_id = request.form.get("user_id")
    hours   = request.form.get("hours")

    # Validación básica: ambos campos son obligatorios
    if not user_id or not hours:
        flash("Datos inválidos")
        return redirect(url_for("admin.admin_panel"))

    # Convierte horas a entero — falla si no es número
    try:
        hours = int(hours)
    except ValueError:
        flash("Horas inválidas")
        return redirect(url_for("admin.admin_panel"))

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        # Calcula la fecha de fin del ban sumando N horas al momento actual
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


# ===============================
# DESBANEAR USUARIO
# Pone banned_until a NULL → el usuario puede volver a loguearse.
# ===============================
@admin_bp.route("/unban_user", methods=["POST"])
@admin_required
def unban_user():

    username = request.form.get("username")

    conn   = get_db_connection()
    cursor = conn.cursor()

    # Elimina la fecha de ban (NULL = sin ban activo)
    cursor.execute(
        "UPDATE users SET banned_until = NULL WHERE username = %s",
        (username,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin.admin_panel"))


# ===============================
# CAMBIAR CONTRASEÑA DE USUARIO
# Cifra la nueva contraseña con Werkzeug antes de guardarla.
# ===============================
@admin_bp.route("/change_password/<username>", methods=["POST"])
@admin_required
def change_password(username):

    new_password = request.form.get("password")

    # Validación: la contraseña no puede estar vacía
    if not new_password:
        flash("Contraseña inválida", "error")
        return redirect(url_for("admin.admin_panel"))

    # Cifra la nueva contraseña antes de guardarla en la BD
    hashed_password = generate_password_hash(new_password)

    conn   = get_db_connection()
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


# ===============================
# API: ESTADÍSTICAS DEL SISTEMA (tiempo real)
# Llamado periódicamente por admin.js para actualizar los gráficos
# sin recargar la página. Devuelve JSON con CPU, RAM, disco y red.
# ===============================
@admin_bp.route("/system_stats")
@admin_required
def system_stats():

    # Obtiene datos del sistema en tiempo real
    cpu  = psutil.cpu_percent(interval=0.5)     # % CPU (muestra rápida)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()

    # Devuelve JSON para consumo desde el frontend (admin.js)
    return jsonify({
        "cpu":          cpu,
        "ram_percent":  ram.percent,
        "ram_used":     round(ram.used  / (1024**3), 2),
        "ram_total":    round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_used":    round(disk.used  / (1024**3), 2),
        "disk_total":   round(disk.total / (1024**3), 2),
        "net_sent":     net.bytes_sent,
        "net_recv":     net.bytes_recv
    })


# ===============================
# API: ESTADÍSTICAS DE BD (tiempo real)
# Llamado por polling desde admin.js para mantener los contadores
# de usuarios, canciones y reproducciones actualizados en directo.
# ===============================
@admin_bp.route("/server_stats_db")
@admin_required
def server_stats_db():

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Total de usuarios registrados
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        # Total de canciones en la plataforma
        cursor.execute("SELECT COUNT(*) AS total_songs FROM songs")
        total_songs = cursor.fetchone()["total_songs"]

        # Total de reproducciones acumuladas
        cursor.execute("SELECT SUM(plays) AS total_plays FROM songs")
        result      = cursor.fetchone()
        total_plays = result["total_plays"] or 0

        # Canción más reproducida
        cursor.execute("SELECT title, plays FROM songs ORDER BY plays DESC LIMIT 1")
        top_song = cursor.fetchone()

        # Usuario con más canciones subidas
        cursor.execute(
            "SELECT username, total_songs FROM users ORDER BY total_songs DESC LIMIT 1"
        )
        top_user = cursor.fetchone()

        return jsonify({
            "total_users":     total_users,
            "total_songs":     total_songs,
            "total_plays":     total_plays,
            "top_song_title":  top_song["title"]       if top_song else None,
            "top_song_plays":  top_song["plays"]       if top_song else None,
            "top_user_name":   top_user["username"]    if top_user else None,
            "top_user_total":  top_user["total_songs"] if top_user else None,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()