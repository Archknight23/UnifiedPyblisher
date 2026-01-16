"""User agent helpers for embedded browser masking."""

import json
import os
import random

CHROME_UA_VERSIONS = (
    "120.0.0.0",
    "121.0.0.0",
    "122.0.0.0",
    "123.0.0.0",
    "124.0.0.0",
    "125.0.0.0",
    "126.0.0.0",
    "127.0.0.0",
)

UA_OS_TEMPLATES = {
    "windows": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{version} Safari/537.36"
    ),
    "mac": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{version} Safari/537.36"
    ),
    "linux": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/{version} Safari/537.36"
    ),
}

PLATFORM_OS_PREFERENCES = {
    "x": ("windows", "mac"),
    "youtube": ("windows", "mac"),
    "default": ("windows", "mac", "linux"),
}


def pick_chrome_version(rng=None):
    """Select a Chrome version for UA masking."""
    rng = rng or random
    return rng.choice(CHROME_UA_VERSIONS)


def build_chrome_user_agent(chrome_version, os_family="linux"):
    """Build a Chrome UA string for embedded browser masking."""
    template = UA_OS_TEMPLATES.get(os_family, UA_OS_TEMPLATES["linux"])
    return template.format(version=chrome_version)


def build_ua_pool(platform=None, versions=None):
    """Build a stable UA pool for deterministic rotation."""
    versions = versions or CHROME_UA_VERSIONS
    os_families = PLATFORM_OS_PREFERENCES.get(platform, PLATFORM_OS_PREFERENCES["default"])
    return [build_chrome_user_agent(version, os_family) for os_family in os_families for version in versions]


def _state_path(state_dir, platform):
    filename = f"ua_state_{platform or 'default'}.json"
    return os.path.join(state_dir, filename)


def _load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle)


def pick_user_agent(platform=None, rng=None, state_dir=None):
    """
    Pick a UA from the platform pool.

    If state_dir is provided, rotate deterministically across the pool.
    """
    pool = build_ua_pool(platform=platform)
    if not pool:
        return build_chrome_user_agent(pick_chrome_version(rng=rng))

    if state_dir:
        path = _state_path(state_dir, platform)
        state = _load_state(path)
        index = int(state.get("index", 0))
        ua = pool[index % len(pool)]
        state["index"] = index + 1
        _save_state(path, state)
        return ua

    rng = rng or random
    return rng.choice(pool)


def extract_chrome_version(user_agent):
    marker = "Chrome/"
    if marker not in user_agent:
        return ""
    start = user_agent.find(marker) + len(marker)
    end = user_agent.find(" ", start)
    if end == -1:
        end = len(user_agent)
    return user_agent[start:end]


def detect_os_family(user_agent):
    if "Windows NT" in user_agent:
        return "windows"
    if "Macintosh" in user_agent:
        return "mac"
    if "X11; Linux" in user_agent:
        return "linux"
    return "unknown"
