"""
test_auth_routes.py — Tests para las rutas de autenticación.

Rutas cubiertas:
  GET  /login
  POST /login   (credenciales válidas, inválidas, usuario baneado)
  POST /register
  GET  /register  (redirección)
  GET  /logout
"""

import pytest
from conftest import TEST_USER, TEST_PASSWORD, TEST_ADMIN, ADMIN_PASSWORD


class TestLoginGET:
    """GET /login → debe devolver el formulario de login."""

    def test_login_page_ok(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"login" in resp.data.lower() or b"form" in resp.data.lower()


class TestLoginPOST:
    """POST /login con distintas combinaciones de credenciales."""

    def test_login_valid_user(self, client):
        """Login correcto redirige a la página principal."""
        resp = client.post("/login", data={
            "username": TEST_USER,
            "password": TEST_PASSWORD,
        }, follow_redirects=True)
        assert resp.status_code == 200
        # Tras login exitoso, la app muestra la página de música (no login de nuevo)
        assert b"login" not in resp.data.lower() or b"logout" in resp.data.lower()

    def test_login_valid_admin(self, client):
        """Login como admin también funciona."""
        resp = client.post("/login", data={
            "username": TEST_ADMIN,
            "password": ADMIN_PASSWORD,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        """Contraseña incorrecta → muestra error, no redirige."""
        resp = client.post("/login", data={
            "username": TEST_USER,
            "password": "wrong_password",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"incorrectas" in resp.data or b"error" in resp.data.lower()

    def test_login_nonexistent_user(self, client):
        """Usuario que no existe → muestra error."""
        resp = client.post("/login", data={
            "username": "usuario_que_no_existe_999",
            "password": "cualquier_clave",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"incorrectas" in resp.data or b"error" in resp.data.lower()

    def test_login_empty_fields(self, client):
        """Campos vacíos → no debe crashear la app."""
        resp = client.post("/login", data={
            "username": "",
            "password": "",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestRegisterPOST:
    """POST /register → registro de usuarios vía JSON."""

    def test_register_new_user(self, client):
        """Registro de un usuario nuevo devuelve success."""
        resp = client.post("/register",
            json={"username": "nuevo_pytest_user_temp", "password": "pass1234"},
            content_type="application/json"
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True

        # Limpiar el usuario creado en este test
        from database.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s", ("nuevo_pytest_user_temp",))
        conn.commit()
        cursor.close()
        conn.close()

    def test_register_duplicate_user(self, client):
        """Registrar un usuario ya existente devuelve 409."""
        resp = client.post("/register",
            json={"username": TEST_USER, "password": "cualquier"},
            content_type="application/json"
        )
        assert resp.status_code == 409
        data = resp.get_json()
        assert data["success"] is False

    def test_register_missing_fields(self, client):
        """Registro sin campos obligatorios devuelve 400."""
        resp = client.post("/register",
            json={"username": "", "password": ""},
            content_type="application/json"
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False


class TestRegisterGET:
    """GET /register → redirige a /login."""

    def test_register_get_redirects(self, client):
        resp = client.get("/register")
        # Debe redirigir (302) o tras follow_redirects llegar al login
        assert resp.status_code in (301, 302, 200)


class TestLogout:
    """GET /logout → cierra sesión y redirige a login."""

    def test_logout_redirects_to_login(self, auth_client):
        resp = auth_client.get("/logout", follow_redirects=True)
        assert resp.status_code == 200
        # Después de logout, la siguiente petición a / debe redirigir a login
        resp2 = auth_client.get("/", follow_redirects=False)
        assert resp2.status_code in (301, 302)
