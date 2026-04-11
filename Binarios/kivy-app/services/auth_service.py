import requests
import config


def check_server() -> bool:
    try:
        r = requests.get(f"{config.SERVER_URL}/login", timeout=config.TIMEOUT)
        return r.status_code < 500
    except Exception:
        return False


def login(username: str, password: str) -> dict:
    try:
        r = requests.post(
            f"{config.SERVER_URL}/login",
            data={"username": username.lower(), "password": password},
            timeout=config.TIMEOUT,
            allow_redirects=False,
        )
        if r.status_code in (302, 200):
            location = r.headers.get("Location", "")
            if "login" not in location:
                # Guardamos las cookies de sesión y el usuario en config
                config.SESSION_COOKIES = dict(r.cookies)
                config.USERNAME = username.lower()
                # Intentar obtener el rol
                _fetch_role()
                return {"success": True}
            return {"success": False, "error": "Credenciales incorrectas"}
        return {"success": False, "error": f"Error del servidor ({r.status_code})"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Tiempo de espera agotado"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _fetch_role():
    """Consulta el rol del usuario al servidor."""
    try:
        r = requests.get(
            f"{config.SERVER_URL}/api/me",
            timeout=config.TIMEOUT,
            cookies=config.SESSION_COOKIES,
        )
        if r.status_code == 200:
            config.ROLE = r.json().get("role", "user")
        else:
            config.ROLE = "user"
    except Exception:
        config.ROLE = "user"


def register(username: str, password: str) -> dict:
    try:
        r = requests.post(
            f"{config.SERVER_URL}/register",
            json={"username": username.lower(), "password": password},
            timeout=config.TIMEOUT,
        )
        return r.json()
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Tiempo de espera agotado"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def logout() -> None:
    try:
        requests.get(
            f"{config.SERVER_URL}/logout",
            timeout=config.TIMEOUT,
            cookies=config.SESSION_COOKIES,
        )
    except Exception:
        pass
    config.SESSION_COOKIES = {}
    config.USERNAME = ""
    config.ROLE = ""
