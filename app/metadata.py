import json
from urllib.parse import quote_plus

import requests


def try_resolve_title(source_url: str) -> str | None:
    trimmed_url = source_url.strip()
    if trimmed_url == "":
        return None

    if "youtube.com" in trimmed_url or "youtu.be" in trimmed_url:
        return _try_resolve_youtube_title_oembed(trimmed_url)

    return None


def _try_resolve_youtube_title_oembed(source_url: str) -> str | None:
    encoded_url = quote_plus(source_url)
    oembed_url = f"https://www.youtube.com/oembed?url={encoded_url}&format=json"

    try:
        response = requests.get(oembed_url, timeout=10)
    except Exception:
        return None

    if response.ok is False:
        return None

    try:
        payload = response.json()
    except Exception:
        return None

    title_text = payload.get("title")
    if isinstance(title_text, str) is False:
        return None

    trimmed_title = title_text.strip()
    if trimmed_title == "":
        return None

    return trimmed_title

