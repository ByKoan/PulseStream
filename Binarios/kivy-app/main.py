import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config
Config.set('graphics', 'width',  '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition

from screens.login_screen import ServerConfigScreen, CheckingScreen, ServerDownScreen, LoginScreen
from screens.index_screen import IndexScreen


class MusicCloudApp(App):
    title = "Music Cloud"

    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.25))
        sm.add_widget(ServerConfigScreen(name="server_config"))
        sm.add_widget(CheckingScreen(name="checking"))
        sm.add_widget(ServerDownScreen(name="server_down"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(IndexScreen(name="index"))
        sm.current = "server_config"
        return sm


if __name__ == "__main__":
    MusicCloudApp().run()
