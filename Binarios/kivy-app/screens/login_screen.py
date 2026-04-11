from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.metrics import dp
import threading
import struct

from services.auth_service import check_server, login, register
import config


# ── Colores CSS ──────────────────────────────────────────────────────────────
CARD_BG   = (0, 0, 0, 0.5)
BTN_BG    = (0, 0, 0, 1)
WHITE     = (1, 1, 1, 1)
GREY      = (0.85, 0.85, 0.85, 1)
ERROR_RED = (1.0, 0.42, 0.42, 1)

# #1d2671  y  #c33764
LEFT  = (0x1d, 0x26, 0x71)
RIGHT = (0xc3, 0x37, 0x64)


# ── Degradado real via textura 2px ──────────────────────────────────────────

def _make_gradient_texture():
    """Crea una textura 2x1 con los dos colores del gradiente."""
    tex = Texture.create(size=(2, 1), colorfmt='rgb')
    # píxel 0 = izquierda (#1d2671), píxel 1 = derecha (#c33764)
    buf = struct.pack('6B', *LEFT, *RIGHT)
    tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
    tex.mag_filter = 'linear'
    tex.min_filter = 'linear'
    return tex


_GRAD_TEX = None   # se crea una sola vez


def draw_gradient(widget):
    """Pinta el fondo del widget con el degradado horizontal del CSS."""
    global _GRAD_TEX
    if _GRAD_TEX is None:
        _GRAD_TEX = _make_gradient_texture()

    with widget.canvas.before:
        Color(1, 1, 1, 1)
        widget._bg_rect = Rectangle(
            texture=_GRAD_TEX,
            pos=widget.pos,
            size=widget.size,
        )

    def _upd(*_):
        widget._bg_rect.pos  = widget.pos
        widget._bg_rect.size = widget.size

    widget.bind(pos=_upd, size=_upd)


# ── Helpers de widgets ───────────────────────────────────────────────────────

def make_label(text, color=WHITE, size=16, bold=False, halign="left"):
    lbl = Label(
        text=text, color=color, font_size=dp(size), bold=bold,
        halign=halign, size_hint_y=None, height=dp(26),
    )
    lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
    return lbl


def make_input(hint, password=False, text=""):
    return TextInput(
        hint_text=hint, text=text, password=password, multiline=False,
        size_hint_y=None, height=dp(42),
        padding=[dp(10), dp(10)],
        background_color=(1, 1, 1, 1),
        foreground_color=(0, 0, 0, 1),
        hint_text_color=(0.5, 0.5, 0.5, 1),
        font_size=dp(15), cursor_color=(0, 0, 0, 1),
    )


def make_button(text):
    btn = Button(
        text=text, size_hint=(1, None), height=dp(44),
        background_color=(0, 0, 0, 0),
        font_size=dp(16), color=WHITE,
    )
    with btn.canvas.before:
        btn._c = Color(*BTN_BG)
        btn._r = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(5)])
    btn.bind(
        pos=lambda i, v: setattr(i._r, "pos", v),
        size=lambda i, v: setattr(i._r, "size", v),
    )
    return btn


def draw_card(widget):
    with widget.canvas.before:
        Color(*CARD_BG)
        widget._bg = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(10)])
    widget.bind(
        pos=lambda i, v: setattr(i._bg, "pos", v),
        size=lambda i, v: setattr(i._bg, "size", v),
    )


# ── Pantallas ────────────────────────────────────────────────────────────────

class ServerConfigScreen(Screen):
    """Pantalla inicial: el usuario introduce IP y puerto antes de conectar."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        draw_gradient(self)

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")

        card = BoxLayout(
            orientation="vertical", padding=dp(32), spacing=dp(12),
            size_hint=(None, None), width=dp(320), height=dp(310),
        )
        draw_card(card)

        card.add_widget(make_label("Configuración del servidor", size=18,
                                   bold=True, halign="center", color=WHITE))

        # Separador visual
        card.add_widget(Label(size_hint_y=None, height=dp(4)))

        card.add_widget(make_label("Dirección IP:", bold=True))
        # Pre-rellena con el valor actual de config.py
        current_url = config.SERVER_URL  # e.g. "http://192.168.1.100:8080"
        default_ip, default_port = self._parse_url(current_url)
        self.ip_input = make_input("192.168.1.100", text=default_ip)
        card.add_widget(self.ip_input)

        card.add_widget(make_label("Puerto:", bold=True))
        self.port_input = make_input("8080", text=default_port)
        card.add_widget(self.port_input)

        self.error_lbl = Label(
            text="", color=ERROR_RED, font_size=dp(12),
            size_hint_y=None, height=dp(18), halign="center",
        )
        self.error_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        card.add_widget(self.error_lbl)

        btn = make_button("Conectar")
        btn.bind(on_press=self.do_connect)
        card.add_widget(btn)

        anchor.add_widget(card)
        self.add_widget(anchor)

    def _parse_url(self, url):
        """Extrae ip y puerto de 'http://ip:puerto'."""
        try:
            parts = url.replace("http://", "").replace("https://", "").split(":")
            return parts[0], parts[1]
        except Exception:
            return "", "8080"

    def do_connect(self, *_):
        ip   = self.ip_input.text.strip()
        port = self.port_input.text.strip()

        if not ip or not port:
            self.error_lbl.text = "Introduce IP y puerto"
            return
        if not port.isdigit():
            self.error_lbl.text = "El puerto debe ser un número"
            return

        # Actualiza la URL en el módulo config en tiempo de ejecución
        config.SERVER_URL = f"http://{ip}:{port}"
        self.error_lbl.text = ""
        self.manager.current = "checking"


class CheckingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        draw_gradient(self)

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        box = BoxLayout(
            orientation="vertical", spacing=dp(10),
            size_hint=(None, None), width=dp(280), height=dp(80),
        )
        box.add_widget(make_label("Music Cloud", size=26, bold=True,
                                  halign="center", color=WHITE))
        self.status_lbl = make_label(
            "Conectando con el servidor...", size=13, color=GREY, halign="center"
        )
        box.add_widget(self.status_lbl)

        anchor.add_widget(box)
        self.add_widget(anchor)

    def on_enter(self):
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        ok = check_server()
        Clock.schedule_once(lambda dt: self._go(ok))

    def _go(self, ok):
        self.manager.current = "login" if ok else "server_down"


class ServerDownScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        draw_gradient(self)

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        card = BoxLayout(
            orientation="vertical", padding=dp(36), spacing=dp(14),
            size_hint=(None, None), width=dp(300), height=dp(230),
        )
        draw_card(card)

        card.add_widget(make_label("Sin conexión", color=WHITE, size=20,
                                   bold=True, halign="center"))
        msg = make_label(
            "Los servidores están caídos o\ninaccesibles. Revisa tu conexión.",
            color=GREY, size=13, halign="center",
        )
        msg.height = dp(46)
        card.add_widget(msg)

        btn_retry = make_button("Reintentar")
        btn_retry.bind(on_press=lambda *_: setattr(self.manager, "current", "checking"))
        card.add_widget(btn_retry)

        btn_config = make_button("Cambiar servidor")
        btn_config.bind(on_press=lambda *_: setattr(self.manager, "current", "server_config"))
        card.add_widget(btn_config)

        anchor.add_widget(card)
        self.add_widget(anchor)


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        draw_gradient(self)

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")

        card = BoxLayout(
            orientation="vertical", padding=dp(32), spacing=dp(10),
            size_hint=(None, None), width=dp(320), height=dp(370),
        )
        draw_card(card)

        card.add_widget(make_label("Iniciar sesión", size=22, bold=True,
                                   halign="center", color=WHITE))

        self.error_lbl = Label(
            text="", color=ERROR_RED, font_size=dp(13),
            size_hint_y=None, height=dp(20), halign="center",
        )
        self.error_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        card.add_widget(self.error_lbl)

        card.add_widget(make_label("Usuario:", bold=True))
        self.username_input = make_input("username")
        card.add_widget(self.username_input)

        card.add_widget(make_label("Contraseña:", bold=True))
        self.password_input = make_input("password", password=True)
        card.add_widget(self.password_input)

        btn_row = BoxLayout(orientation="horizontal", spacing=dp(10),
                            size_hint_y=None, height=dp(44))
        btn_login = make_button("Login")
        btn_login.bind(on_press=self.do_login)
        btn_register = make_button("Register")
        btn_register.bind(on_press=self.do_register)
        btn_row.add_widget(btn_login)
        btn_row.add_widget(btn_register)
        card.add_widget(btn_row)

        anchor.add_widget(card)
        self.add_widget(anchor)

    def show_error(self, msg):
        self.error_lbl.text = msg

    def clear_error(self):
        self.error_lbl.text = ""

    def show_popup(self, title, msg):
        Popup(title=title, content=Label(text=msg, halign="center"),
              size_hint=(0.8, 0.25)).open()

    def do_login(self, *_):
        u = self.username_input.text.strip()
        p = self.password_input.text.strip()
        if not u or not p:
            self.show_error("Todos los campos son obligatorios")
            return
        self.clear_error()
        threading.Thread(target=self._login_thread, args=(u, p), daemon=True).start()

    def _login_thread(self, u, p):
        result = login(u, p)
        Clock.schedule_once(lambda dt: self._on_login(result))

    def _on_login(self, result):
        if result["success"]:
            self.manager.current = 'index'
        else:
            self.show_error(result.get("error", "Error desconocido"))

    def do_register(self, *_):
        u = self.username_input.text.strip()
        p = self.password_input.text.strip()
        if not u or not p:
            self.show_error("Todos los campos son obligatorios")
            return
        self.clear_error()
        threading.Thread(target=self._register_thread, args=(u, p), daemon=True).start()

    def _register_thread(self, u, p):
        result = register(u, p)
        Clock.schedule_once(lambda dt: self._on_register(result))

    def _on_register(self, result):
        if result.get("success"):
            self.show_popup("Registro exitoso", result.get("message", "Usuario creado"))
        else:
            self.show_error(result.get("error", "Error desconocido"))
