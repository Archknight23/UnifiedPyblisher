"""Python based Qt Engine Backend
For use with multilple Social Media Platforms and
for spawning additional social media post sites."""

import json
import os
import sys

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class Bridge(QObject):
    # Talks to HTML frontend and is used to call Python commands from the Java frontend.
    # format: (platform_name, success_Bool, message_string)
    operationFinished = pyqtSignal(str, bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        print("[Bridge]: Your brain is connected to your ass.")

    @pyqtSlot(str, str, result=str)
    def testConnection(self, msg, origin):
        """Are you a liar? This tests if shit is fucked or not."""
        print(f"[Bridge] Handshake from {origin}: {msg}")
        return "Oh shit, it works!~"

    @pyqtSlot(str)
    def handlePublishRequest(self, json_data):
        """Main: Receives shit from JS
        JSON: {content, platform[], image, creds}"""
        print("[Bridge] AYO, they wanna post some cancer")
        try:
            data = json.loads(json_data)
            content = data.get("content", "")
            platforms = data.get("platforms", [])
            image = data.get("image")
            creds = data.get("credentials", {})

            print(f"[Bridge] Posting to: {platforms}")

            # Right now it just says you're a good girl'
            # We'll add real api calls later
            for platform in platforms:
                self.operationFinished.emit(platform, True, "Good girl!")
        except Exception as err:
            print(f"[Bridge] Error: Oh shit baby girl: {err}!")
            self.operationFinished.emit("error", False, str(err))


class UnifiedWindow(QMainWindow):
    # Where the magick lives
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Foundry Central Publishing Service")
        self.resize(1200, 900)

        # Embed Browser
        self.browser = QWebEngineView()

        # BUILD THAT BRIDGE, BRIDGETTE!
        self.channel = QWebChannel()
        self.bridge = Bridge()

        # Register bridge so JS can touch it as pyBridge
        self.channel.registerObject("pyBridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # HTML Load (Next to be created)
        html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
        html_path = os.path.abspath(html_path)
        self.browser.setUrl(QUrl.fromLocalFile(html_path))

        # Setup Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedWindow()
    window.show()
    sys.exit(app.exec())
