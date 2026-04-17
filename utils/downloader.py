"""Download audio from a YouTube URL using yt-dlp."""
import os
import tempfile

import yt_dlp


def download_youtube_audio(youtube_url: str) -> str | None:
    """Download the best audio track for a YouTube URL.

    Returns the local path to the downloaded .m4a/.mp3 file or None on error.
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt2wp_")
    out_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "noprogress": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(filename)[0] + ".mp3"
            return mp3_path if os.path.exists(mp3_path) else filename
    except Exception as e:
        print(f"Errore download: {e}")
        return None
