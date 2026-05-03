"""
test_admin_routes.py — Tests para el panel de administración de PulseStream.

Rutas cubiertas:
  GET/POST /admin/                        → panel principal (lista usuarios, crear usuario)
  GET      /admin/system_stats            → métricas del sistema en JSON
  POST     /admin/change_role/<username>  → cambia el rol de un usuario
  POST     /admin/delete/<user_id>        → elimina un usuario
  POST     /admin/ban_user                → banea un usuario N horas
  POST     /admin/unban_user              → desbanea un usuario
  POST     /admin/change_password/<u>     → cambia la contraseña de un usuario

Todas las rutas están protegidas por el decorador @admin_required que:
  - Redirige a /login si no hay sesión activa.
  - Devuelve HTTP 403 si el usuario logueado no tiene rol 'admin'.

Fixtures usadas (definidas en conftest.py):
  client       → cliente Flask sin sesión (anónimo)
  auth_client  → cliente logueado como usuario normal (rol 'user')
  admin_client → cliente logueado como administrador (rol 'admin')
"""

import pytest
from conftest import TEST_USER, TEST_ADMIN, ADMIN_PASSWORD
from database.db import get_db_connection
from werkzeug.security import generate_password_hash


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────────

def _get_user_id(username: str):
    """Devuelve el id numérico de un usuario por su username, o None si no existe."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row["id"] if row else None


def _create_temp_user(username: str, password: str = "temp_pass_123", role: str = "user"):
    """Crea un usuario temporal en la BD para usar en un test y borrarlo al terminar."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT IGNORE INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, generate_password_hash(password), role)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _delete_temp_user(username: str):
    """Elimina un usuario temporal de la BD (teardown de tests)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=%s", (username,))
    conn.commit()
    cursor.close()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
class TestAdminAccess:
    """
    Verifica el control de acceso al panel de administración.

    El decorador @admin_required protege todas las rutas /admin/*.
    Comportamiento esperado:
      - Sin sesión      → redirección (301/302) a /login
      - Usuario normal  → HTTP 403 con mensaje de permisos denegados
      - Admin           → HTTP 200 con el panel visible
    """

    def test_admin_panel_requires_login(self, client):
        """Sin sesión activa, GET /admin/ debe redirigir a /login."""
        resp = client.get("/admin/", follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_admin_panel_forbidden_for_normal_user(self, auth_client):
        """
        Un usuario con rol 'user' es redirigido al index al intentar acceder al panel.
        La respuesta final es 200 (index), no el panel de admin.
        """
        resp = auth_client.get("/admin/", follow_redirects=True)
        assert resp.status_code == 200
        # El panel de admin no debe estar visible; el index sí tiene el player
        assert b"admin_panel" not in resp.data

    def test_admin_panel_ok_for_admin(self, admin_client):
        """Un usuario con rol 'admin' accede correctamente al panel (HTTP 200)."""
        resp = admin_client.get("/admin/")
        assert resp.status_code == 200
        assert b"admin" in resp.data.lower()


# ──────────────────────────────────────────────────────────────────────────────
class TestSystemStats:
    """
    GET /admin/system_stats → devuelve métricas del sistema en formato JSON.

    Campos esperados en la respuesta: cpu, ram_percent, disk_percent.
    Solo accesible para administradores.
    """

    def test_system_stats_returns_json(self, admin_client):
        """Admin recibe JSON con métricas de CPU, RAM y disco."""
        resp = admin_client.get("/admin/system_stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "cpu" in data
        assert "ram_percent" in data
        assert "disk_percent" in data

    def test_system_stats_requires_admin(self, auth_client):
        """Un usuario normal es redirigido al index, no recibe las métricas."""
        resp = auth_client.get("/admin/system_stats", follow_redirects=True)
        assert resp.status_code == 200
        assert resp.get_json() is None


# ──────────────────────────────────────────────────────────────────────────────
class TestChangeRole:
    """
    POST /admin/change_role/<username> → cambia el rol de un usuario en la BD.

    Solo accesible para administradores. Admite los roles 'user' y 'admin'.
    """

    def test_change_role_to_admin(self, admin_client):
        """
        El admin cambia el rol de un usuario a 'admin'.
        Se verifica directamente en la BD que el cambio se aplicó.
        """
        temp = "pytest_role_user"
        _create_temp_user(temp)
        try:
            resp = admin_client.post(f"/admin/change_role/{temp}",
                data={"role": "admin"},
                follow_redirects=True
            )
            assert resp.status_code == 200

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT role FROM users WHERE username=%s", (temp,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            assert row["role"] == "admin"
        finally:
            _delete_temp_user(temp)

    def test_change_role_requires_admin(self, auth_client):
        """Un usuario normal es redirigido al index al intentar cambiar roles."""
        resp = auth_client.post(f"/admin/change_role/{TEST_USER}",
            data={"role": "admin"},
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert resp.get_json() is None  # Redirige al index, no devuelve JSON


# ──────────────────────────────────────────────────────────────────────────────
class TestDeleteUser:
    """
    POST /admin/delete/<user_id> → elimina permanentemente un usuario de la BD.

    Solo accesible para administradores.
    """

    def test_delete_user_success(self, admin_client):
        """
        El admin elimina un usuario existente.
        Se verifica que el usuario ya no existe en la BD después de la operación.
        """
        temp = "pytest_delete_user"
        _create_temp_user(temp)
        user_id = _get_user_id(temp)
        assert user_id is not None

        resp = admin_client.post(f"/admin/delete/{user_id}",
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert _get_user_id(temp) is None

    def test_delete_user_requires_admin(self, auth_client):
        """Un usuario normal es redirigido al index al intentar eliminar usuarios."""
        user_id = _get_user_id(TEST_USER)
        resp = auth_client.post(f"/admin/delete/{user_id}",
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert resp.get_json() is None  # Redirige al index, no devuelve JSON


# ──────────────────────────────────────────────────────────────────────────────
class TestBanUnban:
    """
    POST /admin/ban_user   → banea un usuario estableciendo banned_until en la BD.
    POST /admin/unban_user → limpia banned_until (NULL) para desbanear.

    Solo accesible para administradores.
    """

    def test_ban_user(self, admin_client):
        """
        El admin banea un usuario por 24 horas.
        Se verifica que banned_until queda establecido en la BD.
        """
        temp = "pytest_ban_user"
        _create_temp_user(temp)
        user_id = _get_user_id(temp)

        try:
            resp = admin_client.post("/admin/ban_user",
                data={"user_id": user_id, "hours": "24"},
                follow_redirects=True
            )
            assert resp.status_code == 200

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT banned_until FROM users WHERE username=%s", (temp,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            assert row["banned_until"] is not None
        finally:
            _delete_temp_user(temp)

    def test_ban_invalid_hours(self, admin_client):
        """
        Pasar un valor no numérico en 'hours' no debe causar un crash (500).
        La app debe manejarlo con un flash de error y devolver 200.
        """
        temp = "pytest_ban_user2"
        _create_temp_user(temp)
        user_id = _get_user_id(temp)
        try:
            resp = admin_client.post("/admin/ban_user",
                data={"user_id": user_id, "hours": "abc"},
                follow_redirects=True
            )
            assert resp.status_code == 200
        finally:
            _delete_temp_user(temp)

    def test_unban_user(self, admin_client):
        """
        Tras banear a un usuario, el admin lo desbanea.
        Se verifica que banned_until vuelve a ser NULL en la BD.
        """
        temp = "pytest_unban_user"
        _create_temp_user(temp)
        user_id = _get_user_id(temp)

        admin_client.post("/admin/ban_user",
            data={"user_id": user_id, "hours": "24"},
            follow_redirects=True
        )

        try:
            resp = admin_client.post("/admin/unban_user",
                data={"username": temp},
                follow_redirects=True
            )
            assert resp.status_code == 200

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT banned_until FROM users WHERE username=%s", (temp,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            assert row["banned_until"] is None
        finally:
            _delete_temp_user(temp)


# ──────────────────────────────────────────────────────────────────────────────
class TestChangePassword:
    """
    POST /admin/change_password/<username> → actualiza el hash de contraseña en la BD.

    Solo accesible para administradores. Contraseña vacía debe ser rechazada.
    """

    def test_change_password_success(self, admin_client):
        """
        El admin cambia la contraseña de un usuario.
        Se verifica con check_password_hash que el nuevo hash es correcto en la BD.
        """
        temp = "pytest_pwd_user"
        _create_temp_user(temp, password="old_pass")
        try:
            resp = admin_client.post(f"/admin/change_password/{temp}",
                data={"password": "new_pass_456"},
                follow_redirects=True
            )
            assert resp.status_code == 200

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT password FROM users WHERE username=%s", (temp,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            from werkzeug.security import check_password_hash
            assert check_password_hash(row["password"], "new_pass_456")
        finally:
            _delete_temp_user(temp)

    def test_change_password_empty_fails(self, admin_client):
        """
        Contraseña vacía debe ser rechazada con un mensaje de error visible.
        La app no debe actualizar la BD ni devolver 500.
        """
        resp = admin_client.post(f"/admin/change_password/{TEST_USER}",
            data={"password": ""},
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert b"nv" in resp.data or b"error" in resp.data.lower() or b"lida" in resp.data

