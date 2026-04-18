"""Download audio from a YouTube URL using yt-dlp.

Note:
- YouTube blocca spesso server cloud con HTTP 403. Per ridurre il rischio
  usiamo i client "ios" e "tv_embedded" (che non richiedono JS runtime) e
  impostiamo uno User-Agent mobile realistico.
- Se si ha accesso a cookies del browser, si possono passare tramite
  la variabile d'ambiente YTDLP_COOKIES_FILE (path a cookies.txt Netscape).
"""
import os
import tempfile

import yt_dlp


UA_IOS = (
    "com.google.ios.youtube/19.09.3 (iPhone16,2; U; CPU iOS 17_4 like Mac OS X)"
)


def download_youtube_audio(youtube_url: str) -> str | None:
    """Download the best audio track for a YouTube URL.

    Returns the local path to the downloaded .mp3 file or None on error.
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt2wp_")
    out_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "noprogress": True,
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "http_headers": {
            "User-Agent": UA_IOS,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                # client senza JS runtime: evita il WARNING su deno e molti 403
                "player_client": ["ios", "tv_embedded", "web_safari"],
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    # Opzionale: cookies da file (Netscape format) per bypassare age-gate/limiti.
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE")
    if cookies_file and os.path.isfile(cookies_file):
        ydl_opts["cookiefile"] = cookies_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(filename)[0] + ".mp3"
            return mp3_path if os.path.exists(mp3_path) else filename
    except Exception as e:
        print(f"Errore download: {e}")
        return None
