"""Bluesky API client helpers."""


def post_to_bluesky(content, handle, password):
    if not content:
        return False, "Empty post"
    if not handle or not password:
        return False, "Missing Bluesky credentials"

    try:
        from atproto import Client
        client = Client()
        client.login(handle, password)
        client.send_post(text=content)
        return True, "Posted"
    except ImportError:
        return False, "Missing dependency: atproto (run: pip install -r requirements.txt)"
    except Exception as exc:
        return False, f"Bluesky error: {exc}"
