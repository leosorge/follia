"""Helper functions: YouTube thumbnail fetch and local file save."""
import os
import re
import tempfile

import requests

OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "yt2wp_output")
TITLE_FILENAME = "titolo.txt"
SINTESI_FILENAME = "sintesi.txt"


def _extract_video_id(youtube_url: str) -> str | None:
    """Extract the 11-char video id from various YouTube URL shapes."""
    # youtu.be/<id>, youtube.com/watch?v=<id>, youtube.com/shorts/<id>
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([\w-]{11})", youtube_url)
    return match.group(1) if match else None


def get_youtube_thumbnail(youtube_url: str) -> bytes | None:
    """Download the YouTube thumbnail, preferring maxresdefault."""
    video_id = _extract_video_id(youtube_url)
    if not video_id:
        return None
    for quality in ("maxresdefault", "hqdefault", "mqdefault", "default"):
        resp = requests.get(
            f"https://img.youtube.com/vi/{video_id}/{quality}.jpg", timeout=10
        )
        if resp.status_code == 200 and resp.content:
            return resp.content
    return None


def save_to_files(points: list[str], title: str, url: str) -> str:
    """Persist title and summary to local files. Returns the output directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sintesi = "\n\n".join(points) + f"\n\nSintesi da <a href='{url}'>video</a>"
    with open(os.path.join(OUTPUT_DIR, SINTESI_FILENAME), "w", encoding="utf-8") as f:
        f.write(sintesi)
    with open(os.path.join(OUTPUT_DIR, TITLE_FILENAME), "w", encoding="utf-8") as f:
        f.write(title)
    return OUTPUT_DIR
