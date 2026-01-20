import json
import tempfile
import unittest
from pathlib import Path

from publisherlogic.credentials import CredentialManager


class TestCredentialManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_dir = Path(self.temp_dir) / ".unifiedpublisher"
        self.storage_dir.mkdir(exist_ok=True)
        self.creds_file = self.storage_dir / "credentials.enc"
        self.key_file = self.storage_dir / ".key"

    def test_initialize_creates_key_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path

            storage_dir = Path(tmpdir) / ".unifiedpublisher"
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.assertTrue(storage_dir.exists())

    def test_save_bluesky_credentials_creates_file(self):
        cm = CredentialManager()
        success = cm.save_bluesky_credentials("user.bsky.social", "test-password")
        self.assertTrue(success)
        self.assertTrue(cm.credentials_file.exists())

    def test_save_and_load_bluesky_credentials(self):
        cm = CredentialManager()
        cm.save_bluesky_credentials("testuser.bsky.social", "app-password-123")

        loaded = cm.load_bluesky_credentials()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["handle"], "testuser.bsky.social")
        self.assertEqual(loaded["password"], "app-password-123")

    def test_save_platform_credentials_x(self):
        cm = CredentialManager()
        session_data = {
            "username": "testuser",
            "avatar": "https://example.com/avatar.png",
            "cookies": {"ct0": "test-token", "guest_id": "v1:12345"},
        }
        success = cm.save_credentials("x", session_data)
        self.assertTrue(success)

        loaded = cm.load_credentials("x")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["username"], "testuser")
        self.assertEqual(loaded["cookies"]["ct0"], "test-token")

    def test_save_and_load_multiple_platforms(self):
        cm = CredentialManager()

        cm.save_credentials(
            "bluesky", {"handle": "user.bsky.social", "password": "pass1"}
        )
        cm.save_credentials("x", {"username": "userx", "cookies": {"auth": "token"}})
        cm.save_credentials("youtube", {"channel_id": "UC12345"})

        bluesky_creds = cm.load_credentials("bluesky")
        x_creds = cm.load_credentials("x")
        youtube_creds = cm.load_credentials("youtube")

        self.assertEqual(bluesky_creds["handle"], "user.bsky.social")
        self.assertEqual(x_creds["username"], "userx")
        self.assertEqual(youtube_creds["channel_id"], "UC12345")

    def test_load_nonexistent_platform_returns_none(self):
        cm = CredentialManager()
        result = cm.load_credentials("nonexistent")
        self.assertIsNone(result)

    def test_has_saved_credentials(self):
        cm = CredentialManager()
        self.assertFalse(cm.has_saved_credentials())

        cm.save_bluesky_credentials("user.bsky.social", "password")
        self.assertTrue(cm.has_saved_credentials())

    def test_delete_credentials_removes_file(self):
        cm = CredentialManager()
        cm.save_bluesky_credentials("user.bsky.social", "password")
        self.assertTrue(cm.credentials_file.exists())

        cm.delete_credentials()
        self.assertFalse(cm.credentials_file.exists())


class TestComposerMethod(unittest.TestCase):
    def test_detect_login_mode_from_url(self):
        login_urls = [
            ("https://x.com/login", True),
            ("https://twitter.com/login", True),
            ("https://www.youtube.com/", True),
            ("https://youtube.com/", True),
            ("https://x.com/compose/post", False),
            ("https://x.com/intent/post?text=test", False),
        ]

        for url, should_have_login in login_urls:
            has_login_keyword = "/login" in url
            is_youtube_base = url.rstrip("/") in [
                "https://www.youtube.com",
                "https://youtube.com",
            ]
            is_login_mode = has_login_keyword or is_youtube_base
            self.assertEqual(is_login_mode, should_have_login, f"Failed for URL: {url}")

    def test_extract_chrome_version_from_ua(self):
        from publisherlogic.user_agent import extract_chrome_version

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        version = extract_chrome_version(ua)
        self.assertEqual(version, "125.0.0.0")

    def test_detect_os_family_from_ua(self):
        from publisherlogic.user_agent import detect_os_family

        windows_ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"
        )
        mac_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/125.0.0.0 Safari/537.36"
        linux_ua = "Mozilla/5.0 (X11; Linux x86_64) Chrome/125.0.0.0 Safari/537.36"

        self.assertEqual(detect_os_family(windows_ua), "windows")
        self.assertEqual(detect_os_family(mac_ua), "mac")
        self.assertEqual(detect_os_family(linux_ua), "linux")


if __name__ == "__main__":
    unittest.main()
