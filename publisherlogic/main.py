"""Python based Qt Engine Backend
For use with multilple Social Media Platforms and
for spawning additional social media post sites."""

import json
import os
import sys

from PyQt6.QtCore import QObject, Qt, QUrl, QDateTime, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from publisherlogic.credentials import CredentialManager
from publisherlogic.user_agent import (
    detect_os_family,
    extract_chrome_version,
    pick_user_agent,
)


class Bridge(QObject):
    # Talks to HTML frontend and is used to call Python commands from the Java frontend.
    # format: (platform_name, success_Bool, message_string)
    operationFinished = pyqtSignal(str, bool, str)

    def __init__(self, main_window, credential_manager=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        # Use shared credential manager from main window
        self.credential_manager = credential_manager or getattr(
            main_window, "credential_manager", None
        )
        if self.credential_manager is None:
            self.credential_manager = CredentialManager()

        print("[Bridge]: Your brain is connected to your ass.")

    @pyqtSlot(str, str)
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

    @pyqtSlot(str)
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

    @pyqtSlot(str)
    def openInternalUrl(self, url):
        """Open a URL inside the app via a docked composer panel."""
        print(f"[Bridge] openInternalUrl called with: {url}")
        if not self.main_window:
            print("[Bridge] No main window reference!")
            return False
        result = self.main_window.open_docked_url(url)
        print(f"[Bridge] Internal URL opened: {result}")
        return result

    @pyqtSlot(str, str)
    def openInternalUrlWithText(self, url, text):
        """Open a URL inside the app and attempt to prefill text."""
        print(f"[Bridge] openInternalUrlWithText called with: {url}")
        if not self.main_window:
            print("[Bridge] No main window reference!")
            return False
        result = self.main_window.open_docked_url(url, prefill_text=text)
        print(f"[Bridge] Internal URL opened (prefill): {result}")
        return result

    @pyqtSlot(str)
    def openDockedUrl(self, url):
        """Open a URL in a DOCKED composer widget within the main window."""
        print(f"[Bridge] openDockedUrl called with: {url}")
        if not self.main_window:
            print("[Bridge] No main window reference!")
            return False
        result = self.main_window.open_docked_composer(url)
        print(f"[Bridge] Docked composer opened: {result}")
        return result

    @pyqtSlot(str, str)
    def openDockedUrlWithText(self, url, text):
        """Open a URL in a docked composer and attempt to prefill text."""
        print(f"[Bridge] openDockedUrlWithText called with: {url}")
        if not self.main_window:
            print("[Bridge] No main window reference!")
            return False
        result = self.main_window.open_docked_composer(url, prefill_text=text)
        print(f"[Bridge] Docked composer opened (prefill): {result}")
        return result

    @pyqtSlot(str, str)
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

    @pyqtSlot()
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

    @pyqtSlot()
    def hasSavedCredentials(self):
        """
        Check if encrypted credentials are saved

        Returns:
            bool: True if credentials exist
        """
        return self.credential_manager.has_saved_credentials()

    @pyqtSlot()
    def deleteSavedCredentials(self):
        """
        Delete saved encrypted credentials

        Returns:
            bool: True if successful
        """
        print("[Bridge] Deleting saved credentials...")
        return self.credential_manager.delete_credentials()

    @pyqtSlot(str)
    def resetPlatformSession(self, platform):
        """Reset stored credentials and profile data for a platform."""
        print(f"[Bridge] Reset platform session requested: {platform}")
        if not self.main_window or not hasattr(self.main_window, "reset_platform_session"):
            print("[Bridge] No main window reset handler available")
            return False
        return self.main_window.reset_platform_session(platform)

    @pyqtSlot(str)
    def setClipboardText(self, text):
        """
        Copy text to system clipboard.

        Args:
            text: The text to copy to clipboard

        Returns:
            bool: True if successful
        """
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)  # type: ignore[attr-defined]
            print(
                f"[Bridge] ✓ Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}"
            )
            return True
        except Exception as err:
            print(f"[Bridge] ✗ Clipboard copy failed: {err}")
            return False

    @pyqtSlot()
    def performJsCleanup(self):
        """
        Trigger JavaScript cleanup on frontend.

        Returns:
            bool: True if cleanup succeeded
        """
        print("[Bridge] Triggering JavaScript cleanup...")
        try:
            if self.main_window and hasattr(self.main_window, "browser"):
                # Call the JavaScript cleanup function
                js_code = "if (typeof performJsCleanup === 'function') { performJsCleanup(); } else { console.log('[Bridge] JavaScript cleanup function not found'); }"
                self.main_window.browser.page().runJavaScript(  # type: ignore[attr-defined]
                    js_code
                )
                return True
            else:
                print("[Bridge] No browser available for JS cleanup")
                return False
        except Exception as err:
            print(f"[Bridge] JavaScript cleanup failed: {err}")
            return False


class ComposerWindow(QMainWindow):
    """Popup window for web composers (X, YouTube, etc.)"""

    def __init__(
        self, url, title="Composer", platform=None, prefill_text=None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Chaos Foundry - {title}")
        self.resize(1000, 700)
        self.platform = platform
        self.parent_window = parent
        self.credential_manager = getattr(parent, "credential_manager", None)
        self.login_detected = False
        self.post_success_signaled = False  # Track if we already signaled post success
        self.prefill_text = prefill_text or ""
        self.prefill_attempts = 0
        self.prefill_completed = False
        self.cookies_restored = False
        self.cookie_jar = {}

        # Detect if this is a login-only flow vs posting flow
        # Login mode: auto-close after detecting login
        # Posting mode: stay open so user can complete their post
        self.is_login_mode = self._detect_login_mode(url)

        # Create web view with isolated profile
        self.profile = self._build_composer_profile()
        self.browser = QWebEngineView()
        page = QWebEnginePage(self.profile, self.browser)
        self.browser.setPage(page)
        self.browser.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        self._setup_cookie_tracking()

        # Inject anti-detection JavaScript when page loads
        self.browser.loadFinished.connect(self._inject_anti_detection)

        # Monitor URL changes and load status
        self.browser.urlChanged.connect(self.check_login_status)
        self.browser.loadFinished.connect(self.on_load_finished)

        # Create glassmorphic header with close button
        header = QWidget()
        header.setMaximumHeight(48)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(12)

        header_title = QLabel(title)
        header_title.setStyleSheet("""
            color: #e0e0e0;
            font-weight: 600;
            font-size: 13px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        """)
        header_layout.addWidget(header_title)
        header_layout.addStretch(1)

        self.status_label = QLabel("⟳ Waiting for login...")
        self.status_label.setStyleSheet("""
            color: #9d4edd;
            font-size: 11px;
            font-weight: 500;
            padding: 4px 10px;
            background: rgba(157, 78, 221, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(157, 78, 221, 0.3);
        """)
        header_layout.addWidget(self.status_label)

        close_button = QPushButton("✕")
        close_button.setFixedSize(32, 32)
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("""
            QPushButton {
                padding: 0px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #e0e0e0;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(239, 71, 111, 0.2);
                border-color: #ef476f;
                color: #ef476f;
            }
            QPushButton:pressed {
                background: rgba(239, 71, 111, 0.3);
            }
        """)
        header_layout.addWidget(close_button)
        header.setLayout(header_layout)
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 255, 255, 0.08),
                stop:1 rgba(255, 255, 255, 0.05));
            border-bottom: 1px solid rgba(255, 255, 255, 0.18);
        """)

        # Container layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(self.browser)
        container.setLayout(layout)

        # Create glassmorphic loading overlay
        self.loading_overlay = QWidget(container)
        loading_layout = QVBoxLayout()
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner using Unicode character
        spinner_label = QLabel("⟳")
        spinner_label.setStyleSheet("""
            color: #9d4edd;
            font-size: 48px;
            font-weight: bold;
        """)
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading text
        loading_text = QLabel("Connecting to Service...")
        loading_text.setStyleSheet("""
            color: #e0e0e0;
            font-size: 13px;
            margin-top: 16px;
            font-weight: 500;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        """)
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        loading_layout.addWidget(spinner_label)
        loading_layout.addWidget(loading_text)
        self.loading_overlay.setLayout(loading_layout)
        self.loading_overlay.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(10, 10, 10, 0.85),
                stop:1 rgba(26, 15, 31, 0.85));
            backdrop-filter: blur(20px);
        """)
        self.loading_overlay.setGeometry(container.geometry())
        self.loading_overlay.raise_()
        self.loading_overlay.show()

        # Load URL
        self._restore_cookies()
        self.browser.setUrl(QUrl(url))

        self.setCentralWidget(container)

    def resizeEvent(self, event):
        """Handle window resize - adjust loading overlay"""
        super().resizeEvent(event)
        if hasattr(self, "loading_overlay") and hasattr(self, "browser"):
            # Position overlay to cover the browser area
            self.loading_overlay.setGeometry(self.browser.geometry())

    def on_load_finished(self, success):
        """Hide loading overlay when page finishes loading"""
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.hide()
        if success:
            self._maybe_prefill()

    def closeEvent(self, event):
        """Handle window close - stop all media playback and signal queue if in posting mode"""
        print(f"[Composer] Closing {self.platform} composer window, stopping media...")

        # If this was a posting flow and we haven't signaled success yet,
        # signal the queue to advance (user manually closed = assume they're done)
        if not self.is_login_mode and not self.post_success_signaled:
            print(
                f"[Composer] Manual close in posting mode - signaling queue to advance"
            )
            self.post_success_signaled = True
            if self.parent_window and hasattr(
                self.parent_window, "on_composer_post_success"
            ):
                self.parent_window.on_composer_post_success(self.platform)

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
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_stop_media
        )

        # Clear the page to force cleanup
        self.browser.setUrl(QUrl("about:blank"))

        # Accept the close event
        event.accept()

    def _build_composer_profile(self):
        """Build isolated web profile for composer - separate per platform"""
        import shutil
        import glob

        # Create platform-specific profile to prevent login conflicts
        profile_name = f"UnifiedPublisher_{self.platform or 'default'}"
        profile = QWebEngineProfile(profile_name, self)

        # Platform-specific storage path
        profile_path = os.path.join(
            os.path.expanduser("~"),
            ".unifiedpublisher",
            f"webprofile_{self.platform or 'default'}",
        )
        os.makedirs(profile_path, exist_ok=True)

        # Rotate UA choices to avoid embed blocking fingerprints
        chrome_user_agent = pick_user_agent(
            platform=self.platform, state_dir=profile_path
        )
        profile.setHttpUserAgent(chrome_user_agent)
        chrome_version = extract_chrome_version(chrome_user_agent)
        os_family = detect_os_family(chrome_user_agent)
        print(f"[Composer] Using UA: {os_family} Chrome/{chrome_version or 'unknown'}")

        # Clear cache directories that cause errors or embed detection
        # Preserve session storage so logins can persist between runs.
        if self.platform in ("x", "youtube"):
            print(f"[Composer] Clearing cache storage for {self.platform}...")

            cache_paths = [
                "GPUCache",
                "DawnWebGPUCache",
                "DawnGraphiteCache",
                "Cache",
            ]

            for item in cache_paths:
                path = os.path.join(profile_path, item)
                if os.path.exists(path):
                    try:
                        shutil.rmtree(path)
                        print(f"[Composer] ✓ Cleared {item}")
                    except Exception as e:
                        print(f"[Composer] ⚠ Could not clear {item}: {e}")

        profile.setCachePath(profile_path)
        profile.setPersistentStoragePath(profile_path)

        # Disable features that reveal we're an embedded browser
        profile.setHttpAcceptLanguage("en-US,en;q=0.9")
        profile.setSpellCheckEnabled(False)

        # Configure profile for better compatibility
        settings = profile.settings()
        settings.setAttribute(settings.WebAttribute.LocalStorageEnabled, True)
        if hasattr(settings.WebAttribute, "CookiesEnabled"):
            settings.setAttribute(settings.WebAttribute.CookiesEnabled, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.JavascriptCanAccessClipboard, True)

        print(f"[Composer] Created profile for {self.platform}: {profile_path}")
        return profile

    def _default_cookie_domain(self):
        return {
            "x": "x.com",
            "youtube": "youtube.com",
            "bluesky": "bsky.app",
        }.get(self.platform or "", "")

    def _cookie_origin_url(self, cookie_data):
        domain = (cookie_data.get("domain") or "").lstrip(".")
        if not domain:
            domain = self._default_cookie_domain()
        if not domain:
            return QUrl()
        scheme = "https" if cookie_data.get("secure", True) else "http"
        return QUrl(f"{scheme}://{domain}")

    def _cookie_from_dict(self, cookie_data):
        try:
            name = cookie_data.get("name")
            value = cookie_data.get("value")
            if not name:
                return None
            cookie = QNetworkCookie()
            cookie.setName(name.encode("utf-8"))
            cookie.setValue((value or "").encode("utf-8"))
            domain = cookie_data.get("domain") or ""
            if domain:
                cookie.setDomain(domain)
            path = cookie_data.get("path") or "/"
            cookie.setPath(path)
            cookie.setSecure(bool(cookie_data.get("secure", False)))
            cookie.setHttpOnly(bool(cookie_data.get("http_only", False)))
            expires = cookie_data.get("expires")
            if expires:
                expiration = QDateTime.fromString(expires, Qt.DateFormat.ISODate)
                if expiration.isValid():
                    cookie.setExpirationDate(expiration)
            return cookie
        except Exception as e:
            print(f"[Composer] ⚠ Failed to restore cookie: {e}")
            return None

    def _cookie_to_dict(self, cookie):
        try:
            expires = cookie.expirationDate()
            expires_str = (
                expires.toString(Qt.DateFormat.ISODate) if expires.isValid() else ""
            )
            return {
                "name": bytes(cookie.name()).decode("utf-8", "ignore"),
                "value": bytes(cookie.value()).decode("utf-8", "ignore"),
                "domain": cookie.domain(),
                "path": cookie.path(),
                "secure": cookie.isSecure(),
                "http_only": cookie.isHttpOnly(),
                "expires": expires_str,
            }
        except Exception as e:
            print(f"[Composer] ⚠ Failed to serialize cookie: {e}")
            return None

    def _setup_cookie_tracking(self):
        try:
            cookie_store = self.profile.cookieStore()
        except Exception as e:
            print(f"[Composer] ⚠ Cookie store unavailable: {e}")
            return
        if hasattr(cookie_store, "cookieAdded"):
            cookie_store.cookieAdded.connect(self._on_cookie_added)
        if hasattr(cookie_store, "cookieRemoved"):
            cookie_store.cookieRemoved.connect(self._on_cookie_removed)
        if hasattr(cookie_store, "loadAllCookies"):
            cookie_store.loadAllCookies()

    def _cookie_key(self, cookie_data):
        if not cookie_data:
            return None
        name = cookie_data.get("name") or ""
        domain = cookie_data.get("domain") or ""
        path = cookie_data.get("path") or ""
        return f"{domain}|{path}|{name}"

    def _store_cookie_data(self, cookie_data):
        key = self._cookie_key(cookie_data)
        if not key:
            return
        self.cookie_jar[key] = cookie_data

    def _on_cookie_added(self, cookie):
        cookie_data = self._cookie_to_dict(cookie)
        if cookie_data:
            self._store_cookie_data(cookie_data)

    def _on_cookie_removed(self, cookie):
        cookie_data = self._cookie_to_dict(cookie)
        key = self._cookie_key(cookie_data)
        if key and key in self.cookie_jar:
            self.cookie_jar.pop(key, None)

    def _normalize_cookie_payload(self, cookies_data):
        normalized = []

        def handle_item(item):
            if not item:
                return
            if isinstance(item, dict):
                normalized.append(item)
                return
            if isinstance(item, list):
                for sub in item:
                    handle_item(sub)
                return
            if isinstance(item, str):
                try:
                    parsed = json.loads(item)
                except Exception:
                    parsed = None
                if isinstance(parsed, (dict, list)):
                    handle_item(parsed)
                    return
                try:
                    parsed_cookies = QNetworkCookie.parseCookies(
                        item.encode("utf-8")
                    )
                except Exception:
                    parsed_cookies = []
                for cookie in parsed_cookies:
                    cookie_data = self._cookie_to_dict(cookie)
                    if cookie_data:
                        normalized.append(cookie_data)
                return

        handle_item(cookies_data)
        return normalized

    def _collect_cookies(self):
        cookies = None
        try:
            cookie_store = self.profile.cookieStore()
            if hasattr(cookie_store, "cookies"):
                cookies = cookie_store.cookies()  # type: ignore[attr-defined]
        except Exception as e:
            print(f"[Composer] ⚠ Failed to read cookies: {e}")
        serialized = []
        if cookies:
            for cookie in cookies:
                item = self._cookie_to_dict(cookie)
                if item:
                    serialized.append(item)
            return serialized
        if self.cookie_jar:
            return list(self.cookie_jar.values())
        return serialized

    def _restore_cookies(self):
        if self.cookies_restored:
            return
        self.cookies_restored = True
        if not self.platform or not self.credential_manager:
            return
        creds = self.credential_manager.load_platform_credentials(self.platform)
        cookies_data = (creds or {}).get("cookies") or []
        cookies_payload = self._normalize_cookie_payload(cookies_data)
        if not cookies_payload:
            return
        try:
            cookie_store = self.profile.cookieStore()
        except Exception as e:
            print(f"[Composer] ⚠ Cookie store unavailable: {e}")
            return
        restored = 0
        for cookie_data in cookies_payload:
            cookie = self._cookie_from_dict(cookie_data)
            if not cookie:
                continue
            origin = self._cookie_origin_url(cookie_data)
            cookie_store.setCookie(cookie, origin)  # type: ignore[attr-defined]
            restored += 1
            self._store_cookie_data(cookie_data)
        print(f"[Composer] Restored {restored} cookies for {self.platform}")

    def _persist_platform_session(self, profile_payload):
        if not self.platform or not self.credential_manager:
            return False
        payload = dict(profile_payload or {})
        payload["cookies"] = self._collect_cookies()
        payload["saved_at"] = QDateTime.currentDateTimeUtc().toString(
            Qt.DateFormat.ISODate
        )
        return self.credential_manager.save_platform_credentials(self.platform, payload)

    def _inject_anti_detection(self):
        """Inject JavaScript to mask Qt WebEngine fingerprints"""
        anti_detection_js = """
        (function() {
            // Override navigator properties that reveal automation
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override plugins to look like regular Chrome
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override mimeTypes
            Object.defineProperty(navigator, 'mimeTypes', {
                get: () => []
            });

            // Mask Chrome runtime
            if (window.chrome) {
                window.chrome.runtime = { onInstalled: {} };
            }

            // Remove webdriver attribute from document
            Object.defineProperty(document, 'webdriver', {
                get: () => undefined
            });

            // Hide automation flags from CSS
            const style = document.createElement('style');
            style.textContent = `
                html::after { content: none !important; }
                body::before { content: none !important; }
            `;
            document.head.appendChild(style);

            console.log('[Anti-detect] Applied navigator overrides');
        })();
        """
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            anti_detection_js
        )

    def _detect_login_mode(self, url):
        """
        Detect if this composer was opened for login-only or for posting.
        Login mode: opened with login URLs, should auto-close after login detected
        Posting mode: opened with compose/post URLs, should stay open for user to post
        """
        url_lower = url.lower()

        # Posting mode indicators - URLs that indicate user wants to compose/post
        posting_indicators = [
            "intent/post",  # X intent URL
            "intent/tweet",  # Legacy Twitter intent
            "compose/post",  # X compose
            "compose/tweet",  # Legacy compose
            "/community",  # YouTube community posts
            "studio.youtube",  # YouTube Studio
            "?text=",  # URL with text parameter (posting)
        ]

        for indicator in posting_indicators:
            if indicator in url_lower:
                print(f"[Composer] Detected POSTING mode (found '{indicator}' in URL)")
                return False  # Not login mode, it's posting mode

        # Login mode indicators - explicit login URLs
        login_indicators = [
            "/login",
            "/signin",
            "accounts.google.com",
            "ServiceLogin",
        ]

        for indicator in login_indicators:
            if indicator in url_lower:
                print(f"[Composer] Detected LOGIN mode (found '{indicator}' in URL)")
                return True  # Login mode

        # Base URLs without path are also login mode (user just wants to login)
        base_urls = [
            "https://x.com/",
            "https://twitter.com/",
            "https://www.youtube.com/",
            "https://youtube.com/",
            "https://bsky.app/",
        ]

        if url in base_urls or url.rstrip("/") + "/" in base_urls:
            print(f"[Composer] Detected LOGIN mode (base URL)")
            return True  # Login mode

        # Default to posting mode (don't auto-close)
        print(f"[Composer] Defaulting to POSTING mode (keep window open)")
        return False

    def _check_auth_callback(self, url_str):
        url = QUrl(url_str)
        if url.scheme() != "unifiedpublisher" or url.host() != "auth":
            return False
        platform = url.path().lstrip("/").split("/")[0]
        if self.platform and platform and platform != self.platform:
            return False
        print(f"[Composer] Auth callback detected for {platform or self.platform}")
        self._handle_login_success()
        return True

    def check_login_status(self, url):
        """Check for login success or post success based on URL changes"""
        url_str = url.toString()
        print(f"[Composer] URL changed to: {url_str}")

        if self._check_auth_callback(url_str):
            return

        # First check for POST SUCCESS (only in posting mode)
        if not self.is_login_mode:
            post_success = self._check_post_success(url_str)
            if post_success:
                return  # Post success handled, don't check login

        # Check for successful login indicators
        logged_in = False

        if self.platform == "x":
            # X/Twitter login detection - check for home feed or compose page
            if (
                "x.com/home" in url_str
                or "twitter.com/home" in url_str
                or "x.com/compose" in url_str
                or "twitter.com/compose" in url_str
            ):
                logged_in = True
                print("[Composer] X login detected, extracting user info...")
                # Delay extraction slightly to let page load
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(1000, self.extract_x_user_info)

        elif self.platform == "youtube":
            # YouTube login detection - detect ANY YouTube page that's not a login page
            # This catches: youtube.com/@handle, youtube.com/feed, youtube.com/channel, studio.youtube.com, etc.
            is_youtube = "youtube.com" in url_str
            is_not_login = (
                "ServiceLogin" not in url_str
                and "accounts.google.com" not in url_str
                and "signin_prompt" not in url_str
                and "signin" not in url_str.lower()
            )
            is_logged_in_page = (
                is_youtube
                and is_not_login
                and (
                    url_str != "https://www.youtube.com/"
                    and url_str != "https://youtube.com/"
                )
            )

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
            is_not_login = (
                "login" not in url_str.lower() and "signin" not in url_str.lower()
            )
            is_logged_in_page = is_bsky and is_not_login

            if is_logged_in_page:
                logged_in = True
                print(f"[Composer] Bluesky logged-in page detected: {url_str}")
                print("[Composer] Extracting profile info...")
                # Delay extraction to let page load
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(2000, self.extract_bluesky_user_info)

        if logged_in:
            self._handle_login_success()

    def _handle_login_success(self):
        if self.login_detected:
            return
        self.login_detected = True
        self.status_label.setText("✓ Logged in successfully!")
        self.status_label.setStyleSheet("""
            color: #06d6a0;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            background: rgba(6, 214, 160, 0.15);
            border-radius: 12px;
            border: 1px solid rgba(6, 214, 160, 0.4);
        """)
        print(f"[Composer] Login confirmed for {self.platform}")

        # Only auto-close in login mode (not when user is trying to post)
        if self.is_login_mode:
            print(f"[Composer] Login mode - auto-closing in 3 seconds...")
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(3000, self.close)
        else:
            print(
                f"[Composer] Posting mode - keeping window open for user to complete post"
            )
            if self.platform == "youtube":
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(1500, self._maybe_prefill)

    def _check_post_success(self, url_str):
        """
        Detect if a post was successfully created based on URL changes.
        Returns True if post success detected.
        """
        import re

        if self.platform == "x":
            # X post success: URL changes to the new tweet URL
            # Pattern: x.com/username/status/1234567890
            if re.search(r"x\.com/\w+/status/\d+", url_str) or re.search(
                r"twitter\.com/\w+/status/\d+", url_str
            ):
                print(f"[Composer] ✓ X POST SUCCESS detected! Tweet URL: {url_str}")
                self._handle_post_success()
                return True

        elif self.platform == "youtube":
            # YouTube community post success is harder to detect
            # After posting, YouTube often stays on the same page or shows a success toast
            # We'll use a different approach: detect navigation away from community page
            # Or detect if user navigates to their channel/feed after posting
            if "/post/" in url_str:
                # YouTube community post URL pattern
                print(
                    f"[Composer] ✓ YouTube POST SUCCESS detected! Post URL: {url_str}"
                )
                self._handle_post_success()
                return True

        return False

    def _handle_post_success(self):
        """Handle successful post - update UI and signal queue to advance"""
        if self.post_success_signaled:
            return  # Already handled

        self.post_success_signaled = True
        self.status_label.setText("✓ Posted successfully!")
        self.status_label.setStyleSheet("""
            color: #06d6a0;
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            background: rgba(6, 214, 160, 0.15);
            border-radius: 12px;
            border: 1px solid rgba(6, 214, 160, 0.4);
        """)
        print(
            f"[Composer] Post success for {self.platform} - closing and advancing queue..."
        )

        # Signal to parent window that post was successful
        if self.parent_window and hasattr(
            self.parent_window, "on_composer_post_success"
        ):
            self.parent_window.on_composer_post_success(self.platform)

        # Auto-close after brief delay to show success message
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(1500, self.close)

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

            const normalized = username.replace(/^@/, '');
            const candidates = [];
            const pushCandidate = (img) => {
                if (!img || !img.src) return;
                if (!img.src.includes('pbs.twimg.com/profile_images')) return;
                if ((img.naturalWidth && img.naturalWidth < 32) || (img.naturalHeight && img.naturalHeight < 32)) return;
                candidates.push(img.src);
            };

            // Extract avatar - prefer account/nav scoped images to avoid random feed avatars
            const navProfileLink = document.querySelector('a[data-testid="AppTabBar_Profile_Link"]');
            if (navProfileLink) {
                pushCandidate(navProfileLink.querySelector('img'));
            }

            const accountSwitcherImg = document.querySelector('[data-testid="SideNav_AccountSwitcher_Button"] img');
            pushCandidate(accountSwitcherImg);

            if (normalized) {
                const userLinkImg = document.querySelector(`a[href="/${normalized}"] img`);
                pushCandidate(userLinkImg);
            }

            if (!candidates.length) {
                const navImg = document.querySelector('nav img[src*="profile_images"]');
                pushCandidate(navImg);
            }

            if (candidates.length) {
                avatarUrl = candidates[0];
            }

            console.log('[X Extraction] Username found:', username, 'Avatar:', avatarUrl);
            return JSON.stringify({username: username, avatar: avatarUrl});
        })();
        """
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_code, self.handle_x_user_info
        )

    def _maybe_prefill(self):
        if not self.prefill_text:
            return
        if self.prefill_completed:
            return
        if self.prefill_attempts >= 5:
            return
        if self.is_login_mode:
            return
        if self.platform != "youtube":
            return
        self._attempt_youtube_prefill()

    def _attempt_youtube_prefill(self):
        self.prefill_attempts += 1
        payload = json.dumps(self.prefill_text)
        js_code = f"""
        (function() {{
            const text = {payload};

            function findTarget() {{
                const selectors = [
                    '#contenteditable-root[contenteditable="true"]',
                    'ytd-backstage-post-dialog-renderer #contenteditable-root',
                    'ytd-backstage-post-dialog-renderer [contenteditable="true"]',
                    'tp-yt-paper-dialog #contenteditable-root',
                    'tp-yt-paper-dialog [contenteditable="true"]'
                ];
                for (const sel of selectors) {{
                    const el = document.querySelector(sel);
                    if (el) return el;
                }}
                return null;
            }}

            function openComposer() {{
                const candidates = Array.from(document.querySelectorAll('ytd-button-renderer, tp-yt-paper-button, button'));
                const match = candidates.find(btn => {{
                    const text = (btn.innerText || btn.textContent || '').toLowerCase();
                    return text.includes('create post') || text.includes('create') || text.includes('post');
                }});
                if (match) {{
                    match.click();
                    return true;
                }}
                return false;
            }}

            let target = findTarget();
            if (!target) {{
                openComposer();
                target = findTarget();
            }}
            if (!target) {{
                return JSON.stringify({{ok: false, reason: 'target_not_found'}});
            }}

            target.focus();
            if (target.isContentEditable) {{
                target.textContent = text;
            }} else if ('value' in target) {{
                target.value = text;
            }}
            target.dispatchEvent(new Event('input', {{ bubbles: true }}));
            return JSON.stringify({{ok: true}});
        }})();
        """
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_code, self._handle_youtube_prefill_result
        )

    def _handle_youtube_prefill_result(self, result_json):
        try:
            data = json.loads(result_json) if result_json else {}
        except Exception:
            data = {}
        ok = bool(data.get("ok"))
        if ok:
            self.prefill_completed = True
            print("[Composer] ✓ YouTube post text injected")
            return

        reason = data.get("reason", "unknown")
        print(
            f"[Composer] YouTube prefill attempt {self.prefill_attempts} failed: {reason}"
        )
        if self.prefill_attempts < 5:
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(1200, self._maybe_prefill)

    def handle_x_user_info(self, data_json):
        """Handle extracted X username and avatar"""
        print(f"[Composer] X data callback received: '{data_json}'")
        try:
            import json

            data = json.loads(data_json)
            username = data.get("username", "")
            avatar = data.get("avatar", "")

            if username:
                print(
                    f"[Composer] ✓ Extracted X username: @{username}, Avatar: {avatar[:50] if avatar else 'none'}"
                )
                saved = self._persist_platform_session(
                    {"handle": username, "avatar": avatar}
                )
                if saved:
                    print("[Composer] ✓ X session cookies saved")
                if self.parent_window and hasattr(self.parent_window, "browser"):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = (
                        avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ""
                    )
                    # Emit signal to update settings in the HTML frontend
                    js_update = f"""
                    console.log('[Composer] Updating X login with username: {username}');
                    if (typeof updateXLoginStatus === 'function') {{
                        updateXLoginStatus('{username}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateXLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(  # type: ignore[attr-defined]
                        js_update
                    )
            else:
                print(f"[Composer] ⚠ Failed to extract X username")
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
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_code, self.handle_youtube_user_info
        )

    def handle_youtube_user_info(self, data_json):
        """Handle extracted YouTube channel handle and avatar"""
        print(f"[Composer] YouTube data callback received: '{data_json}'")
        try:
            import json

            data = json.loads(data_json)
            handle = data.get("handle", "")
            avatar = data.get("avatar", "")

            if handle:
                print(
                    f"[Composer] ✓ Extracted YouTube handle: @{handle}, Avatar: {avatar[:50] if avatar else 'none'}"
                )
                saved = self._persist_platform_session(
                    {"channel_id": handle, "avatar": avatar}
                )
                if saved:
                    print("[Composer] ✓ YouTube session cookies saved")
                if self.parent_window and hasattr(self.parent_window, "browser"):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = (
                        avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ""
                    )
                    js_update = f"""
                    console.log('[Composer] Updating YouTube login with handle: {handle}');
                    if (typeof updateYouTubeLoginStatus === 'function') {{
                        updateYouTubeLoginStatus('{handle}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateYouTubeLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(  # type: ignore[attr-defined]
                        js_update
                    )
            else:
                print(f"[Composer] ⚠ Failed to extract YouTube handle")
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
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_code, self.handle_bluesky_user_info
        )

    def handle_bluesky_user_info(self, data_json):
        """Handle extracted Bluesky handle and avatar"""
        print(f"[Composer] Bluesky data callback received: '{data_json}'")
        try:
            import json

            data = json.loads(data_json)
            handle = data.get("handle", "")
            avatar = data.get("avatar", "")

            if handle and self.parent_window:
                print(
                    f"[Composer] ✓ Extracted Bluesky handle: {handle}, Avatar: {avatar[:50] if avatar else 'none'}"
                )
                # Update parent window to save settings
                if hasattr(self.parent_window, "browser"):
                    # Properly escape avatar URL for JavaScript
                    avatar_escaped = (
                        avatar.replace("'", "\\'").replace('"', '\\"') if avatar else ""
                    )
                    js_update = f"""
                    console.log('[Composer] Updating Bluesky login with handle: {handle}');
                    if (typeof updateBlueskyLoginStatus === 'function') {{
                        updateBlueskyLoginStatus('{handle}', '{avatar_escaped}');
                    }} else {{
                        console.error('[Composer] updateBlueskyLoginStatus function not found!');
                    }}
                    """
                    self.parent_window.browser.page().runJavaScript(  # type: ignore[attr-defined]
                        js_update
                    )
            else:
                print(
                    f"[Composer] ⚠ Failed to extract Bluesky handle or no parent window"
                )
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
        self.platform_windows = {}
        self.credential_manager = CredentialManager()

        # Embed Browser with isolated profile
        self.browser = QWebEngineView()
        profile = QWebEngineProfile("UnifiedPublisher_Main", self.browser)

        # Configure profile to reduce embed detection
        profile.setHttpUserAgent(pick_user_agent(platform="default"))
        profile.setHttpAcceptLanguage("en-US,en;q=0.9")
        profile.setSpellCheckEnabled(False)

        # Set up paths
        main_profile_path = os.path.join(
            os.path.expanduser("~"), ".unifiedpublisher", "webprofile_main"
        )
        os.makedirs(main_profile_path, exist_ok=True)
        profile.setCachePath(main_profile_path)
        profile.setPersistentStoragePath(main_profile_path)

        page = QWebEnginePage(profile, self.browser)
        self.browser.setPage(page)

        settings = self.browser.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)

        # BUILD THAT BRIDGE, BRIDGETTE!
        self.channel = QWebChannel()
        self.bridge = Bridge(self, credential_manager=self.credential_manager)

        # Register bridge so JS can touch it as pyBridge
        self.channel.registerObject("pyBridge", self.bridge)
        self.browser.page().setWebChannel(self.channel)

        # HTML Load (Next to be created)
        html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
        html_path = os.path.abspath(html_path)
        self.browser.setUrl(QUrl.fromLocalFile(html_path))

        # Set browser as central widget (no more docked composer!)
        self.setCentralWidget(self.browser)

    def open_docked_url(self, url, prefill_text=None):
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

            if platform:
                existing = self.platform_windows.get(platform)
                if existing and existing.isVisible():
                    print(f"[Bridge] Reusing {platform} composer window")
                    existing.raise_()
                    existing.activateWindow()
                    existing.is_login_mode = existing._detect_login_mode(url)
                    existing.prefill_text = prefill_text or ""
                    existing.prefill_attempts = 0
                    existing.prefill_completed = False
                    existing.browser.setUrl(QUrl(url))
                    if prefill_text:
                        existing._maybe_prefill()
                    return True
                if existing:
                    self.platform_windows.pop(platform, None)

            # Create and show popup window
            composer = ComposerWindow(
                url,
                title,
                platform=platform,
                prefill_text=prefill_text,
                parent=self,
            )
            composer.show()

            # Track window to prevent garbage collection
            self.composer_windows.append(composer)
            if platform:
                self.platform_windows[platform] = composer

            # Clean up closed windows
            self.composer_windows = [w for w in self.composer_windows if w.isVisible()]

            print(f"[Bridge] Popup composer opened: {title}")
            return True
        except Exception as err:
            print(f"[Bridge] Failed to open popup composer: {err}")
            return False

    def open_docked_composer(self, url, prefill_text=None):
        """Open a URL in a docked composer widget within the main window."""
        try:
            print(f"[Bridge] Opening docked composer for: {url}")

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

            # Create dock widget
            dock = QDockWidget(title, self)
            dock.setAllowedAreas(
                Qt.DockWidgetArea.RightDockWidgetArea
                | Qt.DockWidgetArea.LeftDockWidgetArea
                | Qt.DockWidgetArea.BottomDockWidgetArea
            )

            # Create embedded composer widget
            from PyQt6.QtWidgets import QWidget, QVBoxLayout

            container = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)

            # Create web view for embedded composer
            web_view = QWebEngineView()
            profile = self._build_docked_profile(platform)
            page = QWebEnginePage(profile, web_view)
            web_view.setPage(page)

            # Configure anti-detection
            web_view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            web_view.loadFinished.connect(
                lambda success: self._inject_docked_anti_detection(web_view)
                if success
                else None
            )

            layout.addWidget(web_view)
            container.setLayout(layout)

            dock.setWidget(container)
            dock.setObjectName(f"dock_{platform or 'default'}")
            dock.setMinimumWidth(400)

            # Add dock to right side
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            dock.show()

            # Load the URL
            web_view.setUrl(QUrl(url))

            # Track the dock
            self.dock_composers = getattr(self, "dock_composers", [])
            self.dock_composers.append(dock)

            print(f"[Bridge] Docked composer opened: {title}")
            return True
        except Exception as err:
            print(f"[Bridge] Failed to open docked composer: {err}")
            return False

    def reset_platform_session(self, platform):
        """Clear stored credentials and profile storage for a platform."""
        if not platform:
            return False
        print(f"[Bridge] Resetting platform session for {platform}")

        if self.credential_manager:
            self.credential_manager.delete_platform_credentials(platform)

        if platform in self.platform_windows:
            try:
                self.platform_windows[platform].close()
            except Exception as err:
                print(f"[Bridge] Failed to close {platform} window: {err}")
            self.platform_windows.pop(platform, None)

        base_profile_path = os.path.join(os.path.expanduser("~"), ".unifiedpublisher")
        profile_dirs = [
            f"webprofile_{platform}",
            f"webprofile_docked_{platform}",
        ]
        import shutil

        for dir_name in profile_dirs:
            dir_path = os.path.join(base_profile_path, dir_name)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    print(f"[Bridge] ✓ Removed {dir_name}")
                except Exception as err:
                    print(f"[Bridge] ⚠ Could not remove {dir_name}: {err}")

        return True

    def _build_docked_profile(self, platform):
        """Build a web profile for docked composers."""
        from publisherlogic.user_agent import pick_user_agent

        profile_name = f"UnifiedPublisher_Docked_{platform or 'default'}"
        profile = QWebEngineProfile(profile_name, self)

        # Set user agent
        import os
        from pathlib import Path

        profile_path = (
            Path.home()
            / ".unifiedpublisher"
            / f"webprofile_docked_{platform or 'default'}"
        )
        profile_path.mkdir(parents=True, exist_ok=True)

        chrome_user_agent = pick_user_agent(
            platform=platform, state_dir=str(profile_path)
        )
        profile.setHttpUserAgent(chrome_user_agent)
        profile.setHttpAcceptLanguage("en-US,en;q=0.9")
        profile.setSpellCheckEnabled(False)

        profile.setCachePath(str(profile_path))
        profile.setPersistentStoragePath(str(profile_path))

        return profile

    def _inject_docked_anti_detection(self, web_view):
        """Inject anti-detection JS into docked composer."""
        anti_detection_js = """
        (function() {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'mimeTypes', { get: () => [] });
            Object.defineProperty(document, 'webdriver', { get: () => undefined });
            console.log('[Docked-Antidetect] Applied navigator overrides');
        })();
        """
        web_view.page().runJavaScript(  # type: ignore[attr-defined]
            anti_detection_js
        )

    def on_composer_post_success(self, platform):
        """Called when a composer detects successful post - signals JS queue to advance."""
        print(f"[Bridge] Post success callback for platform: {platform}")
        # Call JavaScript function to mark current queue item as done and advance
        js_code = f"""
        console.log('[Bridge] Post success signal received for: {platform}');
        if (typeof handleComposerPostSuccess === 'function') {{
            handleComposerPostSuccess('{platform}');
        }} else {{
            console.log('[Bridge] handleComposerPostSuccess not found, trying markCurrentDone');
            if (typeof markCurrentDone === 'function') {{
                markCurrentDone();
            }}
        }}
        """
        self.browser.page().runJavaScript(  # type: ignore[attr-defined]
            js_code
        )

    def cleanup_application(self):
        """Perform proper cleanup of WebEngine resources and profiles."""
        print("[Cleanup] Starting application cleanup...")

        try:
            # Close all composer windows first
            if hasattr(self, "composer_windows"):
                print(
                    f"[Cleanup] Closing {len(self.composer_windows)} composer windows..."
                )
                for window in self.composer_windows:
                    try:
                        window.close()
                    except Exception as e:
                        print(f"[Cleanup] Error closing composer window: {e}")
                self.composer_windows.clear()
                self.platform_windows.clear()

            # Close any docked composers
            if hasattr(self, "dock_composers"):
                print(
                    f"[Cleanup] Closing {len(self.dock_composers)} docked composers..."
                )
                for dock in self.dock_composers:
                    try:
                        dock.close()
                    except Exception as e:
                        print(f"[Cleanup] Error closing docked composer: {e}")
                self.dock_composers.clear()

            # Clean up main browser
            if hasattr(self, "browser") and self.browser:
                print("[Cleanup] Cleaning up main browser...")
                try:
                    # Stop all media playback
                    stop_media_js = """
                    // Stop all audio/video elements
                    document.querySelectorAll('audio, video').forEach(el => {
                        el.pause();
                        el.src = '';
                        el.load();
                    });
                    // Clear any ongoing requests
                    if (window.stop) {
                        window.stop();
                    }
                    """
                    self.browser.page().runJavaScript(  # type: ignore[attr-defined]
                        stop_media_js
                    )

                    # Clear the page to force cleanup
                    self.browser.setUrl(QUrl("about:blank"))

                    # Delete the page and view properly
                    page = self.browser.page()
                    if page:
                        page.deleteLater()
                    self.browser.deleteLater()

                except Exception as e:
                    print(f"[Cleanup] Error cleaning up browser: {e}")

            # Clean up WebEngine profiles
            self._cleanup_webengine_profiles()

            # Trigger JavaScript cleanup first
            if hasattr(self, "bridge") and self.bridge:
                print("[Cleanup] Triggering JavaScript cleanup...")
                try:
                    self.bridge.performJsCleanup()
                except Exception as e:
                    print(f"[Cleanup] Error triggering JS cleanup: {e}")

            # Clean up bridge
            if hasattr(self, "bridge") and self.bridge:
                print("[Cleanup] Cleaning up bridge...")
                try:
                    self.bridge.deleteLater()
                except Exception as e:
                    print(f"[Cleanup] Error cleaning up bridge: {e}")

            # Clean up web channel
            if hasattr(self, "channel") and self.channel:
                print("[Cleanup] Cleaning up web channel...")
                try:
                    self.channel.deleteLater()
                except Exception as e:
                    print(f"[Cleanup] Error cleaning up channel: {e}")

            print("[Cleanup] ✅ Application cleanup completed successfully!")

        except Exception as e:
            print(f"[Cleanup] ⚠ Error during cleanup: {e}")

    def _cleanup_webengine_profiles(self):
        """Clean up WebEngine profiles to prevent corruption between runs."""
        print("[Cleanup] Cleaning up WebEngine profiles...")

        try:
            import shutil
            import glob
            import time

            base_profile_path = os.path.join(
                os.path.expanduser("~"), ".unifiedpublisher"
            )
            if not os.path.exists(base_profile_path):
                return

            # Platforms that need cache cleanup
            problematic_platforms = ["x", "youtube", "bluesky"]

            for platform in problematic_platforms:
                # Clean popup composer profiles
                profile_path = os.path.join(base_profile_path, f"webprofile_{platform}")
                if os.path.exists(profile_path):
                    print(f"[Cleanup] Cleaning profile for {platform}...")

                    # Remove cache directories only; preserve session/cookie storage.
                    cache_dirs = [
                        "GPUCache",
                        "DawnWebGPUCache",
                        "DawnGraphiteCache",
                        "Cache",
                    ]

                    for dir_name in cache_dirs:
                        dir_path = os.path.join(profile_path, dir_name)
                        if os.path.exists(dir_path):
                            try:
                                shutil.rmtree(dir_path)
                                print(f"[Cleanup] ✓ Removed {dir_name}")
                            except Exception as e:
                                print(f"[Cleanup] ⚠ Could not remove {dir_name}: {e}")

                    # Clean docked profiles too
                    docked_profile_path = os.path.join(
                        base_profile_path, f"webprofile_docked_{platform}"
                    )
                    if os.path.exists(docked_profile_path):
                        for dir_name in cache_dirs:
                            dir_path = os.path.join(docked_profile_path, dir_name)
                            if os.path.exists(dir_path):
                                try:
                                    shutil.rmtree(dir_path)
                                    print(f"[Cleanup] ✓ Removed docked {dir_name}")
                                except Exception as e:
                                    print(
                                        f"[Cleanup] ⚠ Could not remove docked {dir_name}: {e}"
                                    )

            # Clean main profile but preserve login sessions
            main_profile_path = os.path.join(base_profile_path, "webprofile_main")
            if os.path.exists(main_profile_path):
                # Only clear caches in main profile, preserve login data
                cache_dirs = [
                    "GPUCache",
                    "DawnWebGPUCache",
                    "DawnGraphiteCache",
                    "Cache",
                ]
                for dir_name in cache_dirs:
                    dir_path = os.path.join(main_profile_path, dir_name)
                    if os.path.exists(dir_path):
                        try:
                            shutil.rmtree(dir_path)
                            print(f"[Cleanup] ✓ Removed main {dir_name}")
                        except Exception as e:
                            print(f"[Cleanup] ⚠ Could not remove main {dir_name}: {e}")

        except Exception as e:
            print(f"[Cleanup] ⚠ Error cleaning up profiles: {e}")

    def closeEvent(self, event):
        """Handle window close event with proper cleanup."""
        print("[Cleanup] Window close event triggered")

        # Perform cleanup before closing
        self.cleanup_application()

        # Accept the close event
        event.accept()

        # Force garbage collection
        import gc

        gc.collect()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnifiedWindow()
    window.show()

    # Setup signal handlers for graceful shutdown
    import signal
    import sys

    def signal_handler(signum, frame):
        print(f"\n[Cleanup] Received signal {signum}, performing graceful shutdown...")
        if window:
            window.cleanup_application()
        app.quit()
        sys.exit(0)

    # Register signal handlers for common termination signals
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command

    print("[App] Application started. Press Ctrl+C to force shutdown with cleanup.")

    # Ensure cleanup happens even if app crashes
    exit_code = app.exec()

    # Final cleanup if not already done
    if window:
        window.cleanup_application()

    sys.exit(exit_code)
