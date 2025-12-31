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

        # Initialize credential manager
        from publisherlogic.credentials import CredentialManager
        self.credential_manager = CredentialManager()

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
        print(f"[Bridge] openExternalUrl called with: {url}")
        try:
            result = QDesktopServices.openUrl(QUrl(url))
            print(f"[Bridge] External URL opened: {result}")
            return result
        except Exception as err:
            print(f"[Bridge] Failed to open URL: {err}")
            return False

    @pyqtSlot(str, result=bool)
    def openInternalUrl(self, url):
        """Open a URL inside the app via a docked composer panel."""
        print(f"[Bridge] openInternalUrl called with: {url}")
        if not self.main_window:
            print("[Bridge] No main window reference!")
            return False
        result = self.main_window.open_docked_url(url)
        print(f"[Bridge] Internal URL opened: {result}")
        return result

    @pyqtSlot(str, str, result=bool)
    def testBlueskyConnection(self, handle, password):
        """Test Bluesky credentials by attempting to authenticate."""
        print(f"[Bridge] Testing Bluesky connection for: {handle}")
        try:
            from atproto import Client
            client = Client()
            profile = client.login(handle, password)
            print(f"[Bridge] ✓ Bluesky login successful for: {profile.handle}")

            # Auto-save credentials on successful test
            self.credential_manager.save_credentials(handle, password)

            return True
        except Exception as err:
            print(f"[Bridge] ✗ Bluesky login failed: {err}")
            return False

    @pyqtSlot(result=str)
    def loadSavedCredentials(self):
        """
        Load saved encrypted credentials

        Returns:
            str: JSON string with credentials or empty string if none saved
        """
        print("[Bridge] Loading saved credentials...")
        credentials = self.credential_manager.load_credentials()
        if credentials:
            return json.dumps(credentials)
        return ""

    @pyqtSlot(result=bool)
    def hasSavedCredentials(self):
        """
        Check if encrypted credentials are saved

        Returns:
            bool: True if credentials exist
        """
        return self.credential_manager.has_saved_credentials()

    @pyqtSlot(result=bool)
    def deleteSavedCredentials(self):
        """
        Delete saved encrypted credentials

        Returns:
            bool: True if successful
        """
        print("[Bridge] Deleting saved credentials...")
        return self.credential_manager.delete_credentials()


class ComposerWindow(QMainWindow):
    """Popup window for web composers (X, YouTube, etc.)"""
    def __init__(self, url, title="Composer", platform=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chaos Foundry - {title}")
        self.resize(1000, 700)
        self.platform = platform
        self.parent_window = parent
        self.login_detected = False

        # Create web view with isolated profile
        self.profile = self._build_composer_profile()
        self.browser = QWebEngineView()
        page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(page)
        self.browser.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        # Monitor URL changes and load status
        self.browser.urlChanged.connect(self.check_login_status)
        self.browser.loadFinished.connect(self.on_load_finished)

        # Create header with close button (ultra compact)
        header = QWidget()
        header.setMaximumHeight(28)  # Force compact height
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 3, 8, 3)
        header_layout.setSpacing(6)

        header_title = QLabel(title)
        header_title.setStyleSheet("color: #e5e7eb; font-weight: 500; font-size: 11px;")
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)

        self.status_label = QLabel("Waiting for login...")
        self.status_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        header_layout.addWidget(self.status_label)

        close_button = QPushButton("✕")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                border-radius: 3px;
                background: #1f2937;
                color: #e5e7eb;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #374151;
            }
        """)
        header_layout.addWidget(close_button)
        header.setLayout(header_layout)
        header.setStyleSheet("background: #111827; border-bottom: 1px solid #374151;")

        # Container layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(self.browser)
        container.setLayout(layout)

        # Create loading overlay (compact and transparent)
        self.loading_overlay = QWidget(container)
        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner using Unicode character
        spinner_label = QLabel("⟳")
        spinner_label.setStyleSheet("""
            color: #8b5cf6;
            font-size: 32px;
            font-weight: bold;
        """)
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading text
        loading_text = QLabel("Connecting to Service...")
        loading_text.setStyleSheet("""
            color: #d1d5db;
            font-size: 11px;
            margin-top: 8px;
            font-weight: 500;
        """)
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        loading_layout.addWidget(spinner_label)
        loading_layout.addWidget(loading_text)
        self.loading_overlay.setLayout(loading_layout)
        self.loading_overlay.setStyleSheet("""
            background: rgba(17, 24, 39, 0.75);
        """)
        self.loading_overlay.setGeometry(container.geometry())
        self.loading_overlay.raise_()
        self.loading_overlay.show()

        # Load URL
        self.browser.setUrl(QUrl(url))

        self.setCentralWidget(container)

    def resizeEvent(self, event):
        """Handle window resize - adjust loading overlay"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_overlay') and hasattr(self, 'browser'):
            # Position overlay to cover the browser area
            self.loading_overlay.setGeometry(self.browser.geometry())

    def on_load_finished(self, success):
        """Hide loading overlay when page finishes loading"""
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.hide()

    def closeEvent(self, event):
        """Handle window close - stop all media playback"""
        print(f"[Composer] Closing {self.platform} composer window, stopping media...")

        # Stop all audio/video playback
        js_stop_media = """
        // Stop all audio and video elements
        document.querySelectorAll('audio, video').forEach(el => {
            el.pause();
            el.src = '';
            el.load();
        });

        // Stop Web Audio API contexts
        if (window.AudioContext || window.webkitAudioContext) {
            const audioContexts = [];
            // Note: Can't enumerate all contexts, but stopping media elements should be enough
        }
        """
        self.browser.page().runJavaScript(js_stop_media)

        # Clear the page to force cleanup
        self.browser.setUrl(QUrl("about:blank"))

        # Accept the close event
        event.accept()

    def _build_composer_profile(self):
        """Build isolated web profile for composer - separate per platform"""
        # Create platform-specific profile to prevent login conflicts
        profile_name = f"UnifiedPublisher_{self.platform or 'default'}"
        profile = QWebEngineProfile(profile_name, self)

        # Platform-specific storage path
        profile_path = os.path.join(
            os.path.expanduser("~"),
            ".unifiedpublisher",
            f"webprofile_{self.platform or 'default'}"
        )
        os.makedirs(profile_path, exist_ok=True)
        profile.setCachePath(profile_path)
        profile.setPersistentStoragePath(profile_path)

        print(f"[Composer] Created profile for {self.platform}: {profile_path}")
        return profile

    def check_login_status(self, url):
        """Check if user has successfully logged in"""
        url_str = url.toString()
        print(f"[Composer] URL changed to: {url_str}")

        # Check for successful login indicators
        logged_in = False

        if self.platform == "x":
            # X/Twitter login detection - check for home feed or compose page
            if ("x.com/home" in url_str or
                "twitter.com/home" in url_str or
                "x.com/compose" in url_str or
                "twitter.com/compose" in url_str):
                logged_in = True
                print("[Composer] X login detected, extracting user info...")
                # Delay extraction slightly to let page load
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1000, self.extract_x_user_info)

        elif self.platform == "youtube":
            # YouTube login detection - detect ANY YouTube page that's not a login page
            # This catches: youtube.com/@handle, youtube.com/feed, youtube.com/channel, studio.youtube.com, etc.
            is_youtube = "youtube.com" in url_str
            is_not_login = ("ServiceLogin" not in url_str and
                           "accounts.google.com" not in url_str and
                           "signin_prompt" not in url_str and
                           "signin" not in url_str.lower())
            is_logged_in_page = (is_youtube and is_not_login and
                                (url_str != "https://www.youtube.com/" and
                                 url_str != "https://youtube.com/"))

            if is_logged_in_page:
                logged_in = True
                print(f"[Composer] YouTube logged-in page detected: {url_str}")
                print("[Composer] Extracting channel info...")
                # Delay extraction to let page load
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, self.extract_youtube_user_info)

        elif self.platform == "bluesky":
            # Bluesky login detection - check if we're past login and on a Bluesky page
            is_bsky = "bsky.app" in url_str
            is_not_login = ("login" not in url_str.lower() and "signin" not in url_str.lower())
            is_logged_in_page = is_bsky and is_not_login

            if is_logged_in_page:
                logged_in = True
                print(f"[Composer] Bluesky logged-in page detected: {url_str}")
                print("[Composer] Extracting profile info...")
                # Delay extraction to let page load
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, self.extract_bluesky_user_info)

        if logged_in and not self.login_detected:
            self.login_detected = True
            self.status_label.setText("✓ Logged in successfully!")
            self.status_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600;")
            print(f"[Composer] Login confirmed for {self.platform}")

            # Auto-close after 3 seconds (give more time for extraction)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, self.close)

    def extract_x_user_info(self):
        """Extract X/Twitter username and avatar from session"""
        print("[Composer] Running X username extraction...")
        # Run JavaScript to get username and avatar from page
        js_code = r"""
        (function() {
            // Try to find username in various places
            let username = '';
            let avatarUrl = '';

            // Method 1: Check profile link in nav bar
            const profileLink = document.querySelector('a[data-testid="AppTabBar_Profile_Link"]');
            if (profileLink) {
                const href = profileLink.getAttribute('href');
                if (href) username = href.replace(/\//g, '');
            }

            // Method 2: Check any profile link
            if (!username) {
                const anyProfileLink = document.querySelector('a[href^="/"][aria-label*="Profile"]');
                if (anyProfileLink) {
                    const href = anyProfileLink.getAttribute('href');
                    if (href) username = href.replace(/\//g, '');
                }
            }

            // Method 3: Check URL if on profile page
            if (!username && window.location.pathname.startsWith('/') && window.location.pathname.length > 1) {
                const parts = window.location.pathname.split('/');
                if (parts.length > 1 && parts[1] && !parts[1].includes('home')) {
                    username = parts[1];
                }
            }

            // Extract avatar - look for profile image with multiple methods
            // Method 1: Profile link in navigation
            let avatarImg = document.querySelector('a[data-testid="AppTabBar_Profile_Link"] img');

            // Method 2: Any profile avatar image
            if (!avatarImg || !avatarImg.src) {
                avatarImg = document.querySelector('img[alt*="profile"]');
            }

            // Method 3: Look for avatar in header
            if (!avatarImg || !avatarImg.src) {
                avatarImg = document.querySelector('header img[src*="profile"]');
            }

            // Method 4: Find any image with 'pbs.twimg.com/profile_images' in src
            if (!avatarImg || !avatarImg.src) {
                const allImages = document.querySelectorAll('img');
                for (let img of allImages) {
                    if (img.src && img.src.includes('pbs.twimg.com/profile_images')) {
                        avatarImg = img;
                        break;
                    }
                }
            }

            if (avatarImg && avatarImg.src) {
                avatarUrl = avatarImg.src;
            }

            console.log('[X Extraction] Username found:', username, 'Avatar:', avatarUrl);
            return JSON.stringify({username: username, avatar: avatarUrl});
        })();
        """
        self.browser.page().runJavaScript(js_code, self.handle_x_user_info)

    def handle_x_user_info(self, data_json):
        """Handle extracted X username and avatar"""
        print(f"[Composer] X data callback received: '{data_json}'")
        try:
            import json
            data = json.loads(data_json)
            username = data.get('username', '')
            avatar = data.get('avatar', '')

            if username and self.parent_window:
                print(f"[Composer] ✓ Extracted X username: @{username}, Avatar: {avatar[:50] if avatar else 'none'}")
                # Update parent window's bridge to save settings
                if hasattr(self.parent_window, 'browser'):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ''
                    # Emit signal to update settings in the HTML frontend
                    js_update = f"""
                    console.log('[Composer] Updating X login with username: {username}');
                    if (typeof updateXLoginStatus === 'function') {{
                        updateXLoginStatus('{username}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateXLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(js_update)
            else:
                print(f"[Composer] ⚠ Failed to extract X username or no parent window")
        except Exception as e:
            print(f"[Composer] ⚠ Error parsing X data: {e}")

    def extract_youtube_user_info(self):
        """Extract YouTube channel info and avatar from session"""
        print("[Composer] Running YouTube channel extraction...")
        js_code = """
        (function() {
            let channelHandle = '';
            let avatarUrl = '';

            // Method 1: Try to find channel handle in Studio
            const handleElements = document.querySelectorAll('yt-formatted-string');
            for (let el of handleElements) {
                const text = el.textContent.trim();
                if (text && text.startsWith('@')) {
                    channelHandle = text.substring(1);
                    break;
                }
            }

            // Method 2: Check channel URL
            if (!channelHandle) {
                const channelLinks = document.querySelectorAll('a[href*="/channel/"], a[href*="/@"]');
                for (let link of channelLinks) {
                    const href = link.getAttribute('href');
                    if (href && href.includes('/@')) {
                        const match = href.match(/@([^/?]+)/);
                        if (match) {
                            channelHandle = match[1];
                            break;
                        }
                    }
                }
            }

            // Method 3: Check page URL directly
            if (!channelHandle && window.location.pathname.includes('/@')) {
                const match = window.location.pathname.match(/@([^/?]+)/);
                if (match) {
                    channelHandle = match[1];
                }
            }

            // Extract avatar - look for profile/channel image
            const avatarImg = document.querySelector('img#avatar, img#img, yt-img-shadow img');
            if (avatarImg && avatarImg.src && !avatarImg.src.includes('data:')) {
                avatarUrl = avatarImg.src;
            }

            console.log('[YouTube Extraction] Handle found:', channelHandle, 'Avatar:', avatarUrl);
            return JSON.stringify({handle: channelHandle, avatar: avatarUrl});
        })();
        """
        self.browser.page().runJavaScript(js_code, self.handle_youtube_user_info)

    def handle_youtube_user_info(self, data_json):
        """Handle extracted YouTube channel handle and avatar"""
        print(f"[Composer] YouTube data callback received: '{data_json}'")
        try:
            import json
            data = json.loads(data_json)
            handle = data.get('handle', '')
            avatar = data.get('avatar', '')

            if handle and self.parent_window:
                print(f"[Composer] ✓ Extracted YouTube handle: @{handle}, Avatar: {avatar[:50] if avatar else 'none'}")
                # Update parent window to save settings
                if hasattr(self.parent_window, 'browser'):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ''
                    js_update = f"""
                    console.log('[Composer] Updating YouTube login with handle: {handle}');
                    if (typeof updateYouTubeLoginStatus === 'function') {{
                        updateYouTubeLoginStatus('{handle}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateYouTubeLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(js_update)
            else:
                print(f"[Composer] ⚠ Failed to extract YouTube handle or no parent window")
        except Exception as e:
            print(f"[Composer] ⚠ Error parsing YouTube data: {e}")

    def extract_bluesky_user_info(self):
        """Extract Bluesky profile handle and avatar from session"""
        print("[Composer] Running Bluesky profile extraction...")
        js_code = """
        (function() {
            let handle = '';
            let avatarUrl = '';

            // Method 1: Look for handle in profile link or text
            const handleElements = document.querySelectorAll('[href*="profile"]');
            for (let el of handleElements) {
                const text = el.textContent.trim();
                if (text && text.includes('.bsky.social')) {
                    handle = text;
                    break;
                }
            }

            // Method 2: Check meta tags or page data
            if (!handle) {
                const handleTexts = document.querySelectorAll('*');
                for (let el of handleTexts) {
                    const text = el.textContent.trim();
                    if (text.match(/^[a-zA-Z0-9.-]+\\.bsky\\.social$/)) {
                        handle = text;
                        break;
                    }
                }
            }

            // Method 3: Extract from URL if on profile page
            if (!handle && window.location.pathname.includes('/profile/')) {
                const match = window.location.pathname.match(/\\/profile\\/([^/?]+)/);
                if (match) {
                    handle = match[1];
                }
            }

            // Extract avatar
            const avatarImgs = document.querySelectorAll('img[alt*="avatar"], img[src*="avatar"], img[src*="cdn.bsky.app"]');
            for (let img of avatarImgs) {
                if (img.src && !img.src.includes('data:') && (img.width > 40 || img.height > 40)) {
                    avatarUrl = img.src;
                    break;
                }
            }

            console.log('[Bluesky Extraction] Handle found:', handle, 'Avatar:', avatarUrl);
            return JSON.stringify({handle: handle, avatar: avatarUrl});
        })();
        """
        self.browser.page().runJavaScript(js_code, self.handle_bluesky_user_info)

    def handle_bluesky_user_info(self, data_json):
        """Handle extracted Bluesky handle and avatar"""
        print(f"[Composer] Bluesky data callback received: '{data_json}'")
        try:
            import json
            data = json.loads(data_json)
            handle = data.get('handle', '')
            avatar = data.get('avatar', '')

            if handle and self.parent_window:
                print(f"[Composer] ✓ Extracted Bluesky handle: {handle}, Avatar: {avatar[:50] if avatar else 'none'}")
                # Update parent window to save settings
                if hasattr(self.parent_window, 'browser'):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ''
                    js_update = f"""
                    console.log('[Composer] Updating Bluesky login with handle: {handle}');
                    if (typeof updateBlueskyLoginStatus === 'function') {{
                        updateBlueskyLoginStatus('{handle}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateBlueskyLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(js_update)
            else:
                print(f"[Composer] ⚠ Failed to extract Bluesky handle or no parent window")
        except Exception as e:
            print(f"[Composer] ⚠ Error parsing Bluesky data: {e}")


class UnifiedWindow(QMainWindow):
    # Where the magick lives
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chaos Foundry Central Publishing Service")
        self.resize(1200, 900)

        # Track open composer windows
        self.composer_windows = []

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

        # Set browser as central widget (no more docked composer!)
        self.setCentralWidget(self.browser)

    def open_docked_url(self, url):
        """Open a URL in a popup composer window."""
        try:
            print(f"[Bridge] Opening popup composer for: {url}")

            # Determine title and platform based on URL
            title = "Composer"
            platform = None
            if "x.com" in url or "twitter.com" in url:
                title = "X Composer"
                platform = "x"
            elif "youtube.com" in url:
                title = "YouTube Studio"
                platform = "youtube"
            elif "bsky.app" in url:
                title = "Bluesky Settings"
                platform = "bluesky"

            # Create and show popup window
            composer = ComposerWindow(url, title, platform=platform, parent=self)
            composer.show()

            # Track window to prevent garbage collection
            self.composer_windows.append(composer)

            # Clean up closed windows
            self.composer_windows = [w for w in self.composer_windows if w.isVisible()]

            print(f"[Bridge] Popup composer opened: {title}")
            return True
        except Exception as err:
            print(f"[Bridge] Failed to open popup composer: {err}")
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedWindow()
    window.show()
    sys.exit(app.exec())
