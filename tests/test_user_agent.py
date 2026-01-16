import tempfile
import unittest

from publisherlogic import user_agent


class TestUserAgentHelpers(unittest.TestCase):
    def test_build_chrome_user_agent_includes_version(self):
        version = "123.4.5.6"
        ua = user_agent.build_chrome_user_agent(version, os_family="windows")

        self.assertIn("Mozilla/5.0", ua)
        self.assertIn("AppleWebKit/537.36", ua)
        self.assertIn(f"Chrome/{version}", ua)
        self.assertTrue(ua.endswith("Safari/537.36"))

    def test_pick_chrome_version_uses_known_versions(self):
        class FakeRandom:
            def choice(self, seq):
                return seq[0]

        version = user_agent.pick_chrome_version(FakeRandom())
        self.assertIn(version, user_agent.CHROME_UA_VERSIONS)

    def test_pick_user_agent_rotates_with_state_dir(self):
        pool = user_agent.build_ua_pool(platform="x")
        self.assertGreater(len(pool), 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            ua_first = user_agent.pick_user_agent(platform="x", state_dir=tmpdir)
            ua_second = user_agent.pick_user_agent(platform="x", state_dir=tmpdir)

        self.assertNotEqual(ua_first, ua_second)
        self.assertIn(ua_first, pool)
        self.assertIn(ua_second, pool)

    def test_extract_chrome_version(self):
        ua = "Mozilla/5.0 Chrome/125.0.0.0 Safari/537.36"
        self.assertEqual(user_agent.extract_chrome_version(ua), "125.0.0.0")

    def test_detect_os_family(self):
        windows_ua = user_agent.build_chrome_user_agent("125.0.0.0", os_family="windows")
        mac_ua = user_agent.build_chrome_user_agent("125.0.0.0", os_family="mac")
        linux_ua = user_agent.build_chrome_user_agent("125.0.0.0", os_family="linux")

        self.assertEqual(user_agent.detect_os_family(windows_ua), "windows")
        self.assertEqual(user_agent.detect_os_family(mac_ua), "mac")
        self.assertEqual(user_agent.detect_os_family(linux_ua), "linux")


if __name__ == "__main__":
    unittest.main()
