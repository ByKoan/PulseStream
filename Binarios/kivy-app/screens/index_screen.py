from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
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

import config
from services.music_service import get_songs, get_stream_url, delete_song, add_to_playlist
from services.auth_service import logout


# ── Colores CSS ──────────────────────────────────────────────────────────────
LEFT       = (0x1d, 0x26, 0x71)   # #1d2671
RIGHT      = (0xc3, 0x37, 0x64)   # #c33764
WHITE      = (1, 1, 1, 1)
GREY       = (0.85, 0.85, 0.85, 1)
BLACK      = (0, 0, 0, 1)
SONG_BG    = (0, 0, 0, 1)         # .song-item background
SONG_BTN   = (1, 0.298, 0.298, 1) # #ff4c4c delete
ADD_BTN    = (0.549, 1, 0, 1)     # #8cff00
MENU_BG    = (0, 0, 0, 1)
NAV_GREEN  = (0.424, 1, 0, 1)     # greenyellow menu-toggle
NAV_RED    = (1, 0.298, 0.298, 1) # #ff4c4c logout
DARK_GREY  = (0.267, 0.267, 0.267, 1)  # #444 toggle off


_GRAD_TEX = None

def _make_gradient_texture():
    tex = Texture.create(size=(2, 1), colorfmt='rgb')
    buf = struct.pack('6B', *LEFT, *RIGHT)
    tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
    tex.mag_filter = 'linear'
    tex.min_filter = 'linear'
    return tex


def draw_gradient(widget):
    global _GRAD_TEX
    if _GRAD_TEX is None:
        _GRAD_TEX = _make_gradient_texture()
    with widget.canvas.before:
        Color(1, 1, 1, 1)
        widget._bg_rect = Rectangle(texture=_GRAD_TEX, pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda i, v: setattr(i._bg_rect, 'pos', v),
        size=lambda i, v: setattr(i._bg_rect, 'size', v),
    )


def make_btn(text, bg=BLACK, color=WHITE, size=15, bold=False, height=40, radius=6):
    btn = Button(
        text=text, font_size=dp(size), color=color, bold=bold,
        size_hint_y=None, height=dp(height),
        background_color=(0, 0, 0, 0),
    )
    with btn.canvas.before:
        btn._c = Color(*bg)
        btn._r = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(radius)])
    btn.bind(
        pos=lambda i, v: setattr(i._r, 'pos', v),
        size=lambda i, v: setattr(i._r, 'size', v),
    )
    return btn


def make_label(text, color=WHITE, size=14, bold=False, halign='left', height=24):
    lbl = Label(
        text=text, color=color, font_size=dp(size), bold=bold,
        halign=halign, size_hint_y=None, height=dp(height),
    )
    lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], None)))
    return lbl


# ── Navbar ───────────────────────────────────────────────────────────────────

class Navbar(BoxLayout):
    def __init__(self, screen, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None, height=dp(56),
            padding=[dp(10), dp(8)], spacing=dp(8),
            **kwargs
        )
        self.screen = screen
        self._menu_open = False

        with self.canvas.before:
            Color(0, 0, 0, 0.35)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda i, v: setattr(i._bg, 'pos', v),
            size=lambda i, v: setattr(i._bg, 'size', v),
        )

        # Botón Menu (greenyellow)
        self.menu_btn = make_btn('Menu', bg=NAV_GREEN, color=BLACK, height=38)
        self.menu_btn.size_hint_x = None
        self.menu_btn.width = dp(80)
        self.menu_btn.bind(on_press=self._toggle_menu)
        self.add_widget(self.menu_btn)

        # Spacer
        self.add_widget(Label())

        # Logout (rojo)
        logout_btn = make_btn('Cerrar sesion', bg=NAV_RED, height=38)
        logout_btn.size_hint_x = None
        logout_btn.width = dp(130)
        logout_btn.bind(on_press=self._do_logout)
        self.add_widget(logout_btn)

    def _toggle_menu(self, *_):
        self._menu_open = not self._menu_open
        self.screen.toggle_menu(self._menu_open)

    def _do_logout(self, *_):
        logout()
        self.screen.manager.current = 'login'


class DropdownMenu(BoxLayout):
    """Menu horizontal que se muestra/oculta bajo el navbar."""
    def __init__(self, screen, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None, height=dp(52),
            padding=[dp(10), dp(6)], spacing=dp(8),
            opacity=0,
            **kwargs
        )
        self.screen = screen

        with self.canvas.before:
            Color(*MENU_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
        self.bind(
            pos=lambda i, v: setattr(i._bg, 'pos', v),
            size=lambda i, v: setattr(i._bg, 'size', v),
        )

        # Admin panel (solo si es admin)
        if config.ROLE == 'admin':
            btn_admin = make_btn('Admin', bg=(0.2, 0.2, 0.2, 1), height=36, radius=20)
            btn_admin.size_hint_x = None
            btn_admin.width = dp(80)
            btn_admin.bind(on_press=lambda *_: setattr(screen.manager, 'current', 'admin'))
            self.add_widget(btn_admin)

        for label, target in [('Upload', 'upload'), ('Playlists', 'playlists'), ('Youtube', 'youtube')]:
            btn = make_btn(label, bg=(0.2, 0.2, 0.2, 1), height=36, radius=20)
            btn.size_hint_x = None
            btn.width = dp(90)
            btn.bind(on_press=lambda *_, t=target: setattr(screen.manager, 'current', t))
            self.add_widget(btn)

        # Inicio activo (#8cff00)
        btn_home = make_btn('Inicio', bg=ADD_BTN, color=BLACK, height=36, radius=20)
        btn_home.size_hint_x = None
        btn_home.width = dp(80)
        self.add_widget(btn_home)

    def show(self, visible):
        self.opacity = 1 if visible else 0
        self.disabled = not visible


# ── Toggle Switch ─────────────────────────────────────────────────────────────

class ToggleSwitch(BoxLayout):
    def __init__(self, label_text, callback, **kwargs):
        super().__init__(
            orientation='horizontal', spacing=dp(10),
            size_hint_y=None, height=dp(36),
            **kwargs
        )
        self.active = False
        self.callback = callback

        self.lbl = Label(text=label_text, color=WHITE, font_size=dp(14),
                         size_hint_x=None, width=dp(120))
        self.add_widget(self.lbl)

        # Track
        self.track = BoxLayout(size_hint=(None, None), size=(dp(54), dp(26)))
        with self.track.canvas.before:
            self._track_color = Color(*DARK_GREY)
            self._track_rect = RoundedRectangle(
                pos=self.track.pos, size=self.track.size, radius=[dp(13)]
            )
        self.track.bind(
            pos=lambda i, v: setattr(i.parent._track_rect, 'pos', v),
            size=lambda i, v: setattr(i.parent._track_rect, 'size', v),
        )

        # Knob
        self.knob = BoxLayout(size_hint=(None, None), size=(dp(20), dp(20)))
        with self.knob.canvas.before:
            Color(1, 1, 1, 1)
            self.knob._knob_rect = RoundedRectangle(pos=self.knob.pos, size=self.knob.size, radius=[dp(10)])
        self.knob.bind(
            pos=lambda i, v: setattr(i._knob_rect, 'pos', v),
            size=lambda i, v: setattr(i._knob_rect, 'size', v),
        )
        self.track.add_widget(self.knob)
        self.add_widget(self.track)

        self.bind(on_touch_down=self._on_tap)

    def _on_tap(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.active = not self.active
            self._update_visual()
            self.callback(self.active)

    def _update_visual(self):
        if self.active:
            self._track_color.rgba = (0.114, 0.149, 0.443, 1)
        else:
            self._track_color.rgba = DARK_GREY


# ── Fila de canción ───────────────────────────────────────────────────────────

class SongItem(BoxLayout):
    def __init__(self, filename, playlists, on_play, on_delete, on_add_playlist, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None, height=dp(52),
            padding=[dp(10), dp(6)], spacing=dp(8),
            **kwargs
        )
        self.filename = filename

        with self.canvas.before:
            Color(*SONG_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(
            pos=lambda i, v: setattr(i._bg, 'pos', v),
            size=lambda i, v: setattr(i._bg, 'size', v),
        )

        # Título (ocupa todo el espacio disponible)
        title = Button(
            text=filename, color=WHITE, font_size=dp(13),
            halign='left', text_size=(dp(160), None),
            background_color=(0, 0, 0, 0),
        )
        title.bind(on_press=lambda *_: on_play(filename))
        self.add_widget(title)

        # Borrar
        del_btn = make_btn('Borrar', bg=SONG_BTN, height=36, size=13)
        del_btn.size_hint_x = None
        del_btn.width = dp(62)
        del_btn.bind(on_press=lambda *_: on_delete(filename, self))
        self.add_widget(del_btn)

        # Añadir a playlist (+)
        add_btn = make_btn('+', bg=ADD_BTN, color=BLACK, height=36, size=16, bold=True)
        add_btn.size_hint_x = None
        add_btn.width = dp(38)
        add_btn.bind(on_press=lambda *_: on_add_playlist(filename, playlists))
        self.add_widget(add_btn)


# ── Pantalla principal ────────────────────────────────────────────────────────

class IndexScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._songs = []
        self._playlists = []
        self._current_index = 0
        self._shuffle = False
        self._loop = False
        self._menu_open = False
        self._build_ui()

    def _build_ui(self):
        draw_gradient(self)

        root = BoxLayout(orientation='vertical')

        # ── Navbar ──────────────────────────────────────────────────────────
        self.navbar = Navbar(screen=self)
        root.add_widget(self.navbar)

        # ── Dropdown menu ───────────────────────────────────────────────────
        self.dropdown = DropdownMenu(screen=self)
        self.dropdown.show(False)
        root.add_widget(self.dropdown)

        # ── Área scrollable ─────────────────────────────────────────────────
        scroll = ScrollView()
        self.content = GridLayout(
            cols=1, spacing=dp(10),
            padding=[dp(12), dp(10), dp(12), dp(20)],
            size_hint_y=None,
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        self.add_widget(root)
        self._populate_content()

    def _populate_content(self):
        c = self.content
        c.clear_widgets()

        # Bienvenida
        self.welcome_lbl = make_label(
            f'Bienvenido, {config.USERNAME}', size=20, bold=True,
            halign='center', height=36,
        )
        c.add_widget(self.welcome_lbl)

        # Canción actual
        self.current_lbl = make_label(
            'Cancion actual: -', size=14, color=GREY,
            halign='center', height=26,
        )
        c.add_widget(self.current_lbl)

        # ── Controles de reproducción ────────────────────────────────────
        controls = BoxLayout(
            orientation='horizontal', spacing=dp(8),
            size_hint_y=None, height=dp(44),
        )
        btn_prev = make_btn('Anterior', height=40)
        btn_prev.bind(on_press=lambda *_: self._prev())
        controls.add_widget(btn_prev)

        self.play_btn = make_btn('Reproducir', height=40)
        self.play_btn.bind(on_press=lambda *_: self._play_pause())
        controls.add_widget(self.play_btn)

        btn_next = make_btn('Siguiente', height=40)
        btn_next.bind(on_press=lambda *_: self._next())
        controls.add_widget(btn_next)
        c.add_widget(controls)

        # ── Modos shuffle / loop ─────────────────────────────────────────
        modes = BoxLayout(
            orientation='horizontal', spacing=dp(20),
            size_hint_y=None, height=dp(40),
            padding=[dp(10), 0],
        )
        self.shuffle_toggle = ToggleSwitch('Modo Aleatorio', self._on_shuffle)
        self.loop_toggle    = ToggleSwitch('Modo Bucle',     self._on_loop)
        modes.add_widget(self.shuffle_toggle)
        modes.add_widget(self.loop_toggle)
        c.add_widget(modes)

        # ── Buscador ─────────────────────────────────────────────────────
        search_row = BoxLayout(
            orientation='horizontal', spacing=dp(6),
            size_hint_y=None, height=dp(42),
        )
        self.search_input = TextInput(
            hint_text='Buscar canciones...', multiline=False,
            size_hint_y=None, height=dp(40),
            font_size=dp(14), padding=[dp(8), dp(8)],
            background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1),
        )
        self.search_input.bind(text=self._on_search)

        btn_reset = make_btn('Reiniciar', height=40, size=13)
        btn_reset.size_hint_x = None
        btn_reset.width = dp(80)
        btn_reset.bind(on_press=self._reset_search)
        search_row.add_widget(self.search_input)
        search_row.add_widget(btn_reset)
        c.add_widget(search_row)

        # ── Contenedor de canciones ───────────────────────────────────────
        self.song_list = GridLayout(
            cols=1, spacing=dp(8), size_hint_y=None,
        )
        self.song_list.bind(minimum_height=self.song_list.setter('height'))
        c.add_widget(self.song_list)

        # ── Carga inicial ─────────────────────────────────────────────────
        self._loading_lbl = make_label(
            'Cargando canciones...', color=GREY, halign='center', height=30,
        )
        self.song_list.add_widget(self._loading_lbl)

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    def on_enter(self):
        self.welcome_lbl.text = f'Bienvenido, {config.USERNAME}'
        self._load_songs()

    def _load_songs(self):
        threading.Thread(target=self._fetch_songs, daemon=True).start()

    def _fetch_songs(self):
        result = get_songs()
        Clock.schedule_once(lambda dt: self._on_songs_loaded(result))

    def _on_songs_loaded(self, result):
        self.song_list.clear_widgets()
        if not result['success']:
            self.song_list.add_widget(
                make_label(f"Error: {result['error']}", color=(1, 0.4, 0.4, 1), halign='center')
            )
            return

        self._songs    = result['songs']
        self._playlists = result['playlists']
        self._render_songs(self._songs)

    def _render_songs(self, songs):
        self.song_list.clear_widgets()
        if not songs:
            self.song_list.add_widget(
                make_label('No hay canciones', color=GREY, halign='center')
            )
            return
        for filename in songs:
            item = SongItem(
                filename=filename,
                playlists=self._playlists,
                on_play=self._play_song,
                on_delete=self._confirm_delete,
                on_add_playlist=self._show_playlist_popup,
            )
            self.song_list.add_widget(item)

    # ── Reproducción ─────────────────────────────────────────────────────────

    def _play_song(self, filename):
        if filename in self._songs:
            self._current_index = self._songs.index(filename)
        self.current_lbl.text = f'Cancion actual: {filename}'
        # En Kivy desktop abrimos la URL; en Android usará MediaPlayer (futura mejora)
        url = get_stream_url(filename)
        self.play_btn.text = 'Pausar'

    def _play_pause(self):
        pass  # Se implementará con MediaPlayer en Android

    def _next(self):
        if not self._songs:
            return
        import random
        if self._shuffle:
            self._current_index = random.randint(0, len(self._songs) - 1)
        else:
            self._current_index = (self._current_index + 1) % len(self._songs)
        self._play_song(self._songs[self._current_index])

    def _prev(self):
        if not self._songs:
            return
        import random
        if self._shuffle:
            self._current_index = random.randint(0, len(self._songs) - 1)
        else:
            self._current_index = (self._current_index - 1) % len(self._songs)
        self._play_song(self._songs[self._current_index])

    def _on_shuffle(self, active):
        self._shuffle = active

    def _on_loop(self, active):
        self._loop = active

    # ── Búsqueda ──────────────────────────────────────────────────────────────

    def _on_search(self, instance, value):
        query = value.lower().strip()
        filtered = [s for s in self._songs if query in s.lower()] if query else self._songs
        self._render_songs(filtered)

    def _reset_search(self, *_):
        self.search_input.text = ''
        self._render_songs(self._songs)

    # ── Eliminar canción ──────────────────────────────────────────────────────

    def _confirm_delete(self, filename, item_widget):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(
            text=f'Borrar "{filename}"?', color=WHITE,
            size_hint_y=None, height=dp(40),
        ))
        btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))

        popup = Popup(title='Confirmar', content=content,
                      size_hint=(0.8, 0.3),
                      background_color=(0, 0, 0, 0.9))

        btn_yes = make_btn('Borrar', bg=SONG_BTN, height=36)
        btn_yes.bind(on_press=lambda *_: self._do_delete(filename, item_widget, popup))
        btn_no = make_btn('Cancelar', height=36)
        btn_no.bind(on_press=popup.dismiss)

        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        popup.open()

    def _do_delete(self, filename, item_widget, popup):
        popup.dismiss()
        threading.Thread(
            target=self._delete_thread, args=(filename, item_widget), daemon=True
        ).start()

    def _delete_thread(self, filename, item_widget):
        result = delete_song(filename)
        Clock.schedule_once(lambda dt: self._on_deleted(result, filename, item_widget))

    def _on_deleted(self, result, filename, item_widget):
        if result.get('success'):
            self._songs = [s for s in self._songs if s != filename]
            self.song_list.remove_widget(item_widget)
        else:
            self._show_popup('Error', result.get('error', 'No se pudo borrar'))

    # ── Añadir a playlist ─────────────────────────────────────────────────────

    def _show_playlist_popup(self, filename, playlists):
        if not playlists:
            self._show_popup('Info', 'No tienes playlists creadas')
            return

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))
        popup = Popup(title=f'Añadir "{filename}"', content=content,
                      size_hint=(0.85, 0.6),
                      background_color=(0, 0, 0, 0.9))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        for pl in playlists:
            btn = make_btn(pl['name'], bg=(0.2, 0.2, 0.2, 1), height=40)
            btn.bind(on_press=lambda *_, p=pl: self._do_add_playlist(filename, p, popup))
            grid.add_widget(btn)

        scroll.add_widget(grid)
        content.add_widget(scroll)

        btn_cancel = make_btn('Cancelar', height=38)
        btn_cancel.bind(on_press=popup.dismiss)
        content.add_widget(btn_cancel)
        popup.open()

    def _do_add_playlist(self, filename, playlist, popup):
        popup.dismiss()
        threading.Thread(
            target=self._add_playlist_thread,
            args=(filename, playlist['id'], playlist['name']),
            daemon=True
        ).start()

    def _add_playlist_thread(self, filename, playlist_id, playlist_name):
        result = add_to_playlist(filename, playlist_id)
        Clock.schedule_once(lambda dt: self._on_added_playlist(result, filename, playlist_name))

    def _on_added_playlist(self, result, filename, playlist_name):
        if result.get('success'):
            self._show_popup('Listo', f'"{filename}" añadida a {playlist_name}')
        else:
            self._show_popup('Error', result.get('error', 'No se pudo añadir'))

    # ── Menu ──────────────────────────────────────────────────────────────────

    def toggle_menu(self, visible):
        self._menu_open = visible
        self.dropdown.show(visible)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_popup(self, title, msg):
        Popup(title=title, content=Label(text=msg, halign='center'),
              size_hint=(0.8, 0.25)).open()
