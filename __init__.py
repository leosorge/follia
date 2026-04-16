import re
import os
import requests

OUTPUT_DIR = "output"
TITLE_FILENAME = "titolo.txt"
SINTESI_FILENAME = "sintesi.txt"


def get_youtube_thumbnail(youtube_url: str) -> bytes | None:
    """Scarica la thumbnail del video YouTube in massima risoluzione."""
    match = re.search(r"(?:v=|be/)([\w-]+)", youtube_url)
    if not match:
        return None
    video_id = match.group(1)
    for quality in ("maxresdefault", "hqdefault"):
        resp = requests.get(f"https://img.youtube.com/vi/{video_id}/{quality}.jpg", timeout=10)
        if resp.status_code == 200:
            return resp.content
    return None


def save_to_files(points: list[str], title: str, url: str) -> None:
    """Salva titolo e sintesi in file locali nella cartella output/."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sintesi = "\n\n".join(points) + f"\n\nSintesi da <a href='{url}'>video</a>"
    with open(os.path.join(OUTPUT_DIR, SINTESI_FILENAME), "w", encoding="utf-8") as f:
        f.write(sintesi)
    with open(os.path.join(OUTPUT_DIR, TITLE_FILENAME), "w", encoding="utf-8") as f:
        f.write(title)
