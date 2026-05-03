"""
test_music_routes.py — Tests para las rutas de música de PulseStream.

Rutas cubiertas:
  GET  /             → página principal con lista de canciones (requiere login)
  GET  /play/<filename> → sirve el archivo de audio al reproductor
  POST /delete_song  → elimina una canción del usuario (BD + disco)

Comportamiento esperado:
  - Todas las rutas requieren sesión; sin ella redirigen a /login.
  - /play/<filename> devuelve 404 si el archivo no existe en disco.
  - /delete_song valida la extensión y la presencia del campo filename;
    devuelve 400 en caso de datos inválidos y 403 si no hay sesión.

Helpers internos:
  _insert_song  → inserta una fila en la tabla songs sin crear archivo en disco
  _delete_song_db → elimina la fila de la BD (teardown)
"""

import io
import os
import pytest
from conftest import TEST_USER
from database.db import get_db_connection


# ──────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────────────────────

def _insert_song(filename: str, username: str = TEST_USER):
    """
    Inserta una canción directamente en la BD sin crear el archivo en disco.
    Útil para preparar el estado previo de tests de delete o playlist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO songs (title, filename, uploaded_by, plays) VALUES (%s, %s, %s, 0)",
        (filename, filename, username)
    )
    conn.commit()
    cursor.close()
    conn.close()


def _delete_song_db(filename: str, username: str = TEST_USER):
    """Elimina una canción de la BD. Usado como teardown en tests."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM songs WHERE filename=%s AND uploaded_by=%s",
        (filename, username)
    )
    conn.commit()
    cursor.close()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
class TestIndex:
    """GET / → página principal con la lista de canciones del usuario."""

    def test_index_redirects_if_not_logged(self, client):
        """Sin sesión activa, GET / redirige a /login."""
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code in (301, 302)
        assert b"login" in resp.headers.get("Location", "").encode()

    def test_index_ok_when_logged(self, auth_client):
        """Con sesión activa, GET / devuelve HTTP 200."""
        resp = auth_client.get("/")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
class TestPlaySong:
    """GET /play/<filename> → sirve el archivo de audio o devuelve 404."""

    def test_play_redirects_if_not_logged(self, client):
        """Sin sesión activa, /play/<filename> redirige a /login."""
        resp = client.get("/play/test_song.mp3", follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_play_nonexistent_file_returns_404(self, auth_client):
        """Archivo que no existe en disco → HTTP 404."""
        resp = auth_client.get("/play/cancion_que_no_existe_98765.mp3")
        assert resp.status_code == 404

    def test_play_existing_file(self, auth_client, test_audio_file):
        """
        Copia el MP3 de prueba al directorio del usuario, lo registra en la BD
        y comprueba que GET /play/<filename> lo sirve correctamente (HTTP 200
        con contenido de audio o body no vacío).

        Usa src/resources/test.mp3 a través del fixture test_audio_file.
        Teardown: elimina el archivo de disco y la fila de la BD.
        """
        filename = "test.mp3"
        user_folder = f"/app/music/{TEST_USER}"
        dest = os.path.join(user_folder, filename)

        os.makedirs(user_folder, exist_ok=True)

        import shutil
        shutil.copy(test_audio_file, dest)

        _insert_song(filename)

        try:
            resp = auth_client.get(f"/play/{filename}")
            assert resp.status_code == 200
            assert resp.content_type.startswith("audio") or len(resp.data) > 0
        finally:
            _delete_song_db(filename)
            if os.path.exists(dest):
                os.remove(dest)


# ──────────────────────────────────────────────────────────────────────────────
class TestDeleteSong:
    """POST /delete_song → elimina una canción del usuario de la BD (y del disco si existe)."""

    def test_delete_song_not_logged(self, client):
        """Sin sesión activa → HTTP 403 (acceso denegado)."""
        resp = client.post("/delete_song",
            json={"filename": "cualquiera.mp3"},
            content_type="application/json"
        )
        assert resp.status_code == 403

    def test_delete_song_invalid_extension(self, auth_client):
        """Extensión no permitida (.exe) → HTTP 400 (bad request)."""
        resp = auth_client.post("/delete_song",
            json={"filename": "malicious.exe"},
            content_type="application/json"
        )
        assert resp.status_code == 400

    def test_delete_song_missing_filename(self, auth_client):
        """Body JSON sin el campo 'filename' → HTTP 400 (bad request)."""
        resp = auth_client.post("/delete_song",
            json={},
            content_type="application/json"
        )
        assert resp.status_code == 400

    def test_delete_song_success(self, auth_client):
        """
        Canción existente en BD → se elimina correctamente.
        Verifica que la respuesta es JSON con success=True y que la fila
        ya no existe en la BD después de la operación.
        """
        filename = "pytest_delete_test.mp3"
        _insert_song(filename)

        resp = auth_client.post("/delete_song",
            json={"filename": filename},
            content_type="application/json"
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM songs WHERE filename=%s AND uploaded_by=%s",
            (filename, TEST_USER)
        )
        assert cursor.fetchone() is None
        cursor.close()
        conn.close()

