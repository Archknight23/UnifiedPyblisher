"""Python based Qt Engine Backend
For use with multilple Social Media Platforms and
for spawning additional social media post sites."""

import json
import os
import sys

from PyQt6.QtCore import QObject, Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class Bridge(QObject):
    # Talks to HTML frontend and is used to call Python commands from the Java frontend.
    # format: (platform_name, success_Bool, message_string)
    operationFinished = pyqtSignal(str, bool, str)

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
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
                if platform == "bluesky":
                    try:
                        from publisherlogic.api_bluesky import post_to_bluesky
                    except Exception as import_err:
                        self.operationFinished.emit(
                            platform,
                            False,
                            f"Bluesky setup error: {import_err}",
                        )
                        continue

                    handle = creds.get("bluesky", {}).get("handle", "")
                    password = creds.get("bluesky", {}).get("password", "")
                    success, message = post_to_bluesky(content, handle, password)
                    self.operationFinished.emit(platform, success, message)
                else:
                    self.operationFinished.emit(platform, False, "API disabled")
        except Exception as err:
            print(f"[Bridge] Error: Oh shit baby girl: {err}!")
            self.operationFinished.emit("error", False, str(err))

    @pyqtSlot(str, result=bool)
    def openExternalUrl(self, url):
        """Open an external URL in the user's default browser."""
        try:
            return QDesktopServices.openUrl(QUrl(url))
        except Exception as err:
            print(f"[Bridge] Failed to open URL: {err}")
            return False

    @pyqtSlot(str, result=bool)
    def openInternalUrl(self, url):
        """Open a URL inside the app via a docked composer panel."""
        if not self.main_window:
            return False
        return self.main_window.open_docked_url(url)


class UnifiedWindow(QMainWindow):
    # Where the magick lives
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Foundry Central Publishing Service")
        self.resize(1200, 900)

        # Embed Browser
        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        # BUILD THAT BRIDGE, BRIDGETTE!
        self.channel = QWebChannel()
        self.bridge = Bridge(self)

        # Register bridge so JS can touch it as pyBridge
        self.channel.registerObject("pyBridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # HTML Load (Next to be created)
        html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
        html_path = os.path.abspath(html_path)
        self.browser.setUrl(QUrl.fromLocalFile(html_path))

        # Docked Composer (right panel)
        self.composer_profile = self._build_composer_profile()
        self.composer_view = QWebEngineView()
        composer_page = QWebEnginePage(self.composer_profile, self.composer_view)
        self.composer_view.setPage(composer_page)
        self.composer_view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        composer_header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_title = QLabel("Composer")
        header_title.setStyleSheet("color: #e5e7eb; font-weight: 600;")
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide_docked_composer)
        close_button.setStyleSheet(
            "padding: 6px 12px; border-radius: 6px; background: #1f2937; color: #e5e7eb;"
        )
        header_layout.addWidget(close_button)
        composer_header.setLayout(header_layout)
        composer_header.setStyleSheet("background: #111827;")

        self.composer_container = QWidget()
        composer_layout = QVBoxLayout()
        composer_layout.setContentsMargins(0, 0, 0, 0)
        composer_layout.setSpacing(0)
        composer_layout.addWidget(composer_header)
        composer_layout.addWidget(self.composer_view)
        self.composer_container.setLayout(composer_layout)
        self.composer_container.setMinimumWidth(380)
        self.composer_container.setVisible(False)

        # Setup Layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.browser)
        splitter.addWidget(self.composer_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([900, 0])

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _build_composer_profile(self):
        profile = QWebEngineProfile("UnifiedPublisherComposer", self)
        profile_path = os.path.join(os.path.expanduser("~"), ".unifiedpublisher", "webprofile")
        os.makedirs(profile_path, exist_ok=True)
        profile.setCachePath(profile_path)
        profile.setPersistentStoragePath(profile_path)
        return profile

    def open_docked_url(self, url):
        """Open a URL inside the docked composer panel."""
        try:
            self.composer_view.setUrl(QUrl(url))
            self.composer_container.setVisible(True)
            return True
        except Exception as err:
            print(f"[Bridge] Failed to open internal URL: {err}")
            return False

    def hide_docked_composer(self):
        self.composer_container.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedWindow()
    window.show()
    sys.exit(app.exec())
