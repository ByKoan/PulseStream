import requests
import config


def get_songs() -> dict:
    """Obtiene la lista de canciones del usuario."""
    try:
        r = requests.get(
            f"{config.SERVER_URL}/api/songs",
            timeout=config.TIMEOUT,
            cookies=config.SESSION_COOKIES,
        )
        if r.status_code == 200:
            return {"success": True, "songs": r.json().get("songs", []), "playlists": r.json().get("playlists", [])}
        return {"success": False, "error": f"Error {r.status_code}"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Tiempo de espera agotado"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_stream_url(filename: str) -> str:
    """Devuelve la URL de streaming de una canción."""
    return f"{config.SERVER_URL}/play/{requests.utils.quote(filename)}"


def delete_song(filename: str) -> dict:
    try:
        r = requests.post(
            f"{config.SERVER_URL}/delete_song",
            json={"filename": filename},
            timeout=config.TIMEOUT,
            cookies=config.SESSION_COOKIES,
        )
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def add_to_playlist(filename: str, playlist_id: int) -> dict:
    try:
        r = requests.post(
            f"{config.SERVER_URL}/add_to_playlist",
            json={"filename": filename, "playlist_id": playlist_id},
            timeout=config.TIMEOUT,
            cookies=config.SESSION_COOKIES,
        )
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
