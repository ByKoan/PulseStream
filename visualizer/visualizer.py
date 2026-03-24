import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)

browser = QWebEngineView()

print("Introduce aqui la URL <ip_vm>:")
URL = input()
browser.setUrl(QUrl(URL))

browser.resize(1200, 800)
browser.setWindowTitle("MusicCloudServer")

browser.show()

sys.exit(app.exec())