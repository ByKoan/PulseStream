"""
conftest.py - Fixtures compartidas para todos los tests de PulseStream.

El contenedor de tests monta src/ en /app (igual que el webserver),
así que los módulos de la app están disponibles directamente en PYTHONPATH.

Fixtures:
  app             → instancia Flask configurada para testing (scope=session)
  setup_test_users→ crea usuarios de prueba antes de los tests y los limpia al terminar
  client          → cliente Flask sin sesión activa (usuario anónimo)
  auth_client     → cliente Flask logueado como usuario normal (rol 'user')
  admin_client    → cliente Flask logueado como administrador (rol 'admin')
  test_audio_file → ruta a un MP3 real en /app/resources/test.mp3 para tests de upload/play

Usuarios de prueba (creados y destruidos automáticamente):
  pytest_user  / pytest_pass_123       → rol 'user'
  pytest_admin / pytest_admin_pass_123 → rol 'admin'

Nota: test_audio_file apunta a /app/resources/test.mp3, que es un MP3 mínimo
incluido en el repositorio (src/resources/test.mp3). No depende de archivos
de música del usuario, por lo que funciona en cualquier entorno limpio.
"""

import os
import sys
import pytest

# La app está en /app dentro del contenedor (COPY src/ /app/ en Dockerfile)
APP_DIR = os.environ.get("APP_DIR", "/app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# ── Variables de entorno (sobreescribibles desde docker-compose) ───────────
os.environ.setdefault("DB_HOST",           "db")
os.environ.setdefault("DB_USER",           "root")
os.environ.setdefault("DB_PASSWORD",       "root")
os.environ.setdefault("DB_NAME",           "music_db")
os.environ.setdefault("SECRET_KEY",        "test_secret_key_pytest")
os.environ.setdefault("BASE_MUSIC_FOLDER", "/app/music")

from main import create_app
from database.db import get_db_connection
from werkzeug.security import generate_password_hash

# ── Usuarios de prueba ─────────────────────────────────────────────────────
TEST_USER      = "pytest_user"
TEST_PASSWORD  = "pytest_pass_123"
TEST_ADMIN     = "pytest_admin"
ADMIN_PASSWORD = "pytest_admin_pass_123"


@pytest.fixture(scope="session")
def app():
    """
    Crea y configura la instancia Flask para la sesión de tests.
    TESTING=True desactiva el manejo de errores de Flask para que pytest
    capture las excepciones directamente.
    """
    application = create_app()
    application.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    return application


@pytest.fixture(scope="session", autouse=True)
def setup_test_users(app):
    """
    Fixture de sesión que se ejecuta automáticamente antes de cualquier test.
    - Setup:    crea pytest_user (rol 'user') y pytest_admin (rol 'admin') en la BD.
    - Teardown: elimina ambos usuarios y sus canciones al terminar todos los tests.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM users WHERE username IN (%s, %s)",
        (TEST_USER, TEST_ADMIN)
    )
    conn.commit()
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')",
        (TEST_USER, generate_password_hash(TEST_PASSWORD))
    )
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, 'admin')",
        (TEST_ADMIN, generate_password_hash(ADMIN_PASSWORD))
    )
    conn.commit()
    cursor.close()
    conn.close()

    yield

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM songs WHERE uploaded_by IN (%s, %s)",
        (TEST_USER, TEST_ADMIN)
    )
    cursor.execute(
        "DELETE FROM users WHERE username IN (%s, %s)",
        (TEST_USER, TEST_ADMIN)
    )
    conn.commit()
    cursor.close()
    conn.close()


@pytest.fixture
def client(app):
    """Cliente Flask sin sesión activa. Simula un usuario anónimo."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_client(app):
    """
    Cliente Flask logueado como usuario normal (rol 'user').
    Realiza el POST /login antes de ceder el cliente al test.
    """
    with app.test_client() as c:
        c.post("/login", data={
            "username": TEST_USER,
            "password": TEST_PASSWORD,
        }, follow_redirects=True)
        yield c


@pytest.fixture
def admin_client(app):
    """
    Cliente Flask logueado como administrador (rol 'admin').
    Realiza el POST /login antes de ceder el cliente al test.
    """
    with app.test_client() as c:
        c.post("/login", data={
            "username": TEST_ADMIN,
            "password": ADMIN_PASSWORD,
        }, follow_redirects=True)
        yield c


@pytest.fixture(scope="session")
def test_audio_file():
    """
    Devuelve la ruta a un MP3 real para tests de upload y reproducción.

    Usa /app/resources/test.mp3, un MP3 mínimo válido incluido en el
    repositorio en src/resources/test.mp3. No depende de archivos de música
    del usuario ni de volúmenes externos, por lo que funciona en cualquier
    entorno limpio sin configuración adicional.
    """
    audio_path = "/app/resources/test.mp3"
    assert os.path.isfile(audio_path), (
        f"Archivo de prueba no encontrado: {audio_path}\n"
        "Asegurate de que src/resources/test.mp3 existe en el repositorio."
    )
    return audio_path

