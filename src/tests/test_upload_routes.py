"""
test_upload_routes.py — Tests para la ruta de subida de canciones.

Rutas cubiertas:
  GET  /upload  → formulario de subida (requiere login)
  POST /upload  → procesa uno o varios archivos de audio

El endpoint POST /upload:
  - Requiere sesión activa; sin ella redirige a /login.
  - Acepta solo extensiones permitidas (.mp3, .wav, etc.); rechaza el resto.
  - Guarda el archivo en /app/music/<username>/ y registra la canción en la BD.
  - Rechaza archivos con nombre vacío sin causar un error 500.

Para el test de subida real (test_upload_valid_mp3_real_file) se usa el fixture
test_audio_file, que apunta a /app/resources/test.mp3 — un MP3 mínimo válido
incluido en el repositorio. No requiere volúmenes externos ni música de usuario.
"""

import io
import os
import pytest
from conftest import TEST_USER
from database.db import get_db_connection


# ──────────────────────────────────────────────────────────────────────────────
class TestUploadGET:
    """GET /upload → formulario de subida (requiere login)."""

    def test_upload_page_redirects_if_not_logged(self, client):
        """Sin sesión activa, GET /upload redirige a /login."""
        resp = client.get("/upload", follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_upload_page_ok_when_logged(self, auth_client):
        """Con sesión activa, GET /upload devuelve 200 con el formulario."""
        resp = auth_client.get("/upload")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
class TestUploadPOST:
    """POST /upload → sube uno o varios archivos de audio al servidor."""

    def test_upload_no_file_field(self, auth_client):
        """
        POST sin el campo 'file' → la app responde con error (200, 302 o 400).
        No debe causar un crash 500.
        """
        resp = auth_client.post("/upload",
            data={},
            content_type="multipart/form-data"
        )
        assert resp.status_code in (200, 302, 400)

    def test_upload_invalid_extension(self, auth_client):
        """
        Archivo con extensión no permitida (.exe) → rechazado.
        Se verifica que el archivo NO se inserta en la BD.
        """
        data = {
            "file": (io.BytesIO(b"fake content"), "malware.exe")
        }
        resp = auth_client.post("/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert resp.status_code == 200

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s AND uploaded_by=%s",
            ("malware.exe", TEST_USER)
        )
        assert cursor.fetchone() is None
        cursor.close()
        conn.close()

    def test_upload_valid_mp3_real_file(self, auth_client, test_audio_file):
        """
        Sube el MP3 de prueba (src/resources/test.mp3) vía multipart/form-data.

        Verifica que:
          1. La respuesta es HTTP 200 (o redirección exitosa).
          2. La canción aparece en la BD del usuario (tabla songs).
          3. El archivo existe físicamente en /app/music/<usuario>/.

        El test es idempotente: borra la canción de la BD y del disco antes
        y después de ejecutarse.
        """
        filename = "test.mp3"

        # Limpiar estado previo para que el test sea repetible
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, TEST_USER)
        )
        conn.commit()
        cursor.close()
        conn.close()

        user_folder = f"/app/music/{TEST_USER}"
        dest = os.path.join(user_folder, filename)
        if os.path.exists(dest):
            os.remove(dest)

        # Leer el MP3 real y enviarlo como multipart
        with open(test_audio_file, "rb") as f:
            audio_bytes = f.read()

        data = {
            "file": (io.BytesIO(audio_bytes), filename)
        }

        resp = auth_client.post("/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert resp.status_code == 200

        # Verificar que se insertó en la BD
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, TEST_USER)
        )
        song = cursor.fetchone()
        assert song is not None, "La canción no se insertó en la BD"
        cursor.close()
        conn.close()

        # Verificar que el archivo existe en disco
        assert os.path.isfile(dest), f"El archivo no existe en disco: {dest}"

        # Teardown: limpiar BD y disco
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, TEST_USER)
        )
        conn.commit()
        cursor.close()
        conn.close()
        if os.path.exists(dest):
            os.remove(dest)

    def test_upload_empty_filename(self, auth_client):
        """
        Archivo con nombre vacío → la app lo ignora sin dar error 500.
        Acepta 200, 302 o 400 como respuesta válida.
        """
        data = {
            "file": (io.BytesIO(b""), "")
        }
        resp = auth_client.post("/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        assert resp.status_code in (200, 302, 400)

