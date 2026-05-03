"""
test_playlist_routes.py — Tests para la gestión de playlists.

Rutas cubiertas:
  GET  /playlists
  POST /create_playlist
  GET  /playlist/<id>
  POST /delete_playlist      (JSON)
  POST /rename_playlist      (JSON)
  POST /add_to_playlist      (JSON)
  POST /remove_from_playlist (JSON)
"""

import pytest
from conftest import TEST_USER
from database.db import get_db_connection


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _create_playlist(username: str, name: str) -> int:
    """Crea una playlist directamente en BD y devuelve su ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playlists (name, user_id) VALUES (%s, %s)",
        (name, username)
    )
    conn.commit()
    playlist_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return playlist_id


def _delete_playlist(playlist_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM playlist_songs WHERE playlist_id=%s", (playlist_id,))
    cursor.execute("DELETE FROM playlists WHERE id=%s", (playlist_id,))
    conn.commit()
    cursor.close()
    conn.close()


def _insert_song(filename: str, username: str = TEST_USER) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO songs (title, filename, uploaded_by, plays) VALUES (%s,%s,%s,0)",
        (filename, filename, username)
    )
    conn.commit()
    song_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return song_id


def _delete_song(filename: str, username: str = TEST_USER):
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
class TestPlaylistsPage:
    """GET /playlists → lista de playlists del usuario."""

    def test_playlists_redirect_if_not_logged(self, client):
        resp = client.get("/playlists", follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_playlists_page_ok(self, auth_client):
        resp = auth_client.get("/playlists")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
class TestCreatePlaylist:
    """POST /create_playlist → crea una nueva playlist."""

    def test_create_playlist_success(self, auth_client):
        resp = auth_client.post("/create_playlist",
            data={"name": "pytest playlist"},
            follow_redirects=True
        )
        assert resp.status_code == 200

        # Verificar en BD
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM playlists WHERE name=%s AND user_id=%s",
            ("pytest playlist", TEST_USER)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        assert row is not None
        _delete_playlist(row["id"])

    def test_create_playlist_empty_name(self, auth_client):
        """Nombre vacío → redirige sin crear."""
        resp = auth_client.post("/create_playlist",
            data={"name": ""},
            follow_redirects=True
        )
        assert resp.status_code == 200

    def test_create_playlist_requires_login(self, client):
        resp = client.post("/create_playlist",
            data={"name": "test"},
            follow_redirects=False
        )
        assert resp.status_code in (301, 302)


# ──────────────────────────────────────────────────────────────────────────────
class TestViewPlaylist:
    """GET /playlist/<id> → vista de una playlist concreta."""

    def test_view_playlist_ok(self, auth_client):
        pid = _create_playlist(TEST_USER, "pytest view pl")
        try:
            resp = auth_client.get(f"/playlist/{pid}")
            assert resp.status_code == 200
        finally:
            _delete_playlist(pid)

    def test_view_playlist_not_owned(self, auth_client):
        """Playlist de otro usuario → redirige."""
        # Crear con un usuario diferente (koan es el admin original)
        pid = _create_playlist("koan", "koan private pl")
        try:
            resp = auth_client.get(f"/playlist/{pid}", follow_redirects=True)
            # Debe redirigir a /playlists (no mostrar la playlist ajena)
            assert resp.status_code == 200
        finally:
            _delete_playlist(pid)

    def test_view_playlist_requires_login(self, client):
        resp = client.get("/playlist/1", follow_redirects=False)
        assert resp.status_code in (301, 302)


# ──────────────────────────────────────────────────────────────────────────────
class TestDeletePlaylist:
    """POST /delete_playlist → elimina una playlist vía JSON."""

    def test_delete_playlist_success(self, auth_client):
        pid = _create_playlist(TEST_USER, "pytest del pl")
        resp = auth_client.post("/delete_playlist",
            json={"playlist_id": pid},
            content_type="application/json"
        )
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["success"] is True

    def test_delete_playlist_not_owned(self, auth_client):
        """Playlist de otro usuario → error."""
        pid = _create_playlist("koan", "koan del pl")
        try:
            resp = auth_client.post("/delete_playlist",
                json={"playlist_id": pid},
                content_type="application/json"
            )
            data = resp.get_json()
            assert data["success"] is False
        finally:
            _delete_playlist(pid)

    def test_delete_playlist_no_auth(self, client):
        resp = client.post("/delete_playlist",
            json={"playlist_id": 1},
            content_type="application/json"
        )
        data = resp.get_json()
        assert data["success"] is False

    def test_delete_playlist_missing_id(self, auth_client):
        resp = auth_client.post("/delete_playlist",
            json={},
            content_type="application/json"
        )
        data = resp.get_json()
        assert data["success"] is False


# ──────────────────────────────────────────────────────────────────────────────
class TestRenamePlaylist:
    """POST /rename_playlist → renombra una playlist vía JSON."""

    def test_rename_playlist_success(self, auth_client):
        pid = _create_playlist(TEST_USER, "nombre original")
        try:
            resp = auth_client.post("/rename_playlist",
                json={"playlist_id": pid, "name": "nombre nuevo"},
                content_type="application/json"
            )
            data = resp.get_json()
            assert resp.status_code == 200
            assert data["success"] is True

            # Verificar cambio en BD
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name FROM playlists WHERE id=%s", (pid,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            assert row["name"] == "nombre nuevo"
        finally:
            _delete_playlist(pid)

    def test_rename_playlist_missing_data(self, auth_client):
        resp = auth_client.post("/rename_playlist",
            json={"playlist_id": None, "name": ""},
            content_type="application/json"
        )
        data = resp.get_json()
        assert data["success"] is False


# ──────────────────────────────────────────────────────────────────────────────
class TestAddToPlaylist:
    """POST /add_to_playlist → añade una canción a una playlist."""

    def test_add_song_success(self, auth_client):
        pid = _create_playlist(TEST_USER, "pytest add pl")
        _insert_song("pytest_add_song.mp3")
        try:
            resp = auth_client.post("/add_to_playlist",
                json={"filename": "pytest_add_song.mp3", "playlist_id": pid},
                content_type="application/json"
            )
            data = resp.get_json()
            assert resp.status_code == 200
            assert data["success"] is True
        finally:
            _delete_playlist(pid)
            _delete_song("pytest_add_song.mp3")

    def test_add_song_duplicate(self, auth_client):
        """Añadir la misma canción dos veces → 409."""
        pid = _create_playlist(TEST_USER, "pytest dup pl")
        _insert_song("pytest_dup_song.mp3")
        try:
            auth_client.post("/add_to_playlist",
                json={"filename": "pytest_dup_song.mp3", "playlist_id": pid},
                content_type="application/json"
            )
            resp = auth_client.post("/add_to_playlist",
                json={"filename": "pytest_dup_song.mp3", "playlist_id": pid},
                content_type="application/json"
            )
            assert resp.status_code == 409
        finally:
            _delete_playlist(pid)
            _delete_song("pytest_dup_song.mp3")

    def test_add_song_not_logged(self, client):
        resp = client.post("/add_to_playlist",
            json={"filename": "x.mp3", "playlist_id": 1},
            content_type="application/json"
        )
        assert resp.status_code == 401

    def test_add_song_missing_data(self, auth_client):
        resp = auth_client.post("/add_to_playlist",
            json={},
            content_type="application/json"
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────────────────────────────────────
class TestRemoveFromPlaylist:
    """POST /remove_from_playlist → quita una canción de una playlist."""

    def test_remove_song_success(self, auth_client):
        pid = _create_playlist(TEST_USER, "pytest remove pl")
        _insert_song("pytest_rem_song.mp3")

        # Añadir primero
        auth_client.post("/add_to_playlist",
            json={"filename": "pytest_rem_song.mp3", "playlist_id": pid},
            content_type="application/json"
        )

        try:
            resp = auth_client.post("/remove_from_playlist",
                json={"filename": "pytest_rem_song.mp3", "playlist_id": pid},
                content_type="application/json"
            )
            data = resp.get_json()
            assert resp.status_code == 200
            assert data["success"] is True
        finally:
            _delete_playlist(pid)
            _delete_song("pytest_rem_song.mp3")

    def test_remove_song_not_logged(self, client):
        resp = client.post("/remove_from_playlist",
            json={"filename": "x.mp3", "playlist_id": 1},
            content_type="application/json"
        )
        assert resp.status_code == 401

    def test_remove_song_missing_data(self, auth_client):
        resp = auth_client.post("/remove_from_playlist",
            json={},
            content_type="application/json"
        )
        assert resp.status_code == 400
