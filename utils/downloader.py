"""Download audio from a YouTube URL using yt-dlp.

YouTube blocca spesso i download con HTTP 403 o "Sign in to confirm you're
not a bot". Le contromisure in ordine di efficacia:

1. Cookies dal browser (migliore su locale): impostare la variabile
   d'ambiente YTDLP_BROWSER al nome del browser installato
   (chrome, firefox, edge, brave, chromium, safari, opera, vivaldi).
   yt-dlp leggera' i cookies YouTube dal profilo attivo del browser.

2. Cookies da file (migliore su server/Streamlit Cloud): esportare un
   cookies.txt in formato Netscape (es. con l'estensione
   "Get cookies.txt LOCALLY") e puntare la variabile
   YTDLP_COOKIES_FILE al percorso del file.

3. Fallback: senza cookies proviamo con client mweb e ios, ma molti
   video privati/age-gated falliranno.
"""
import os
import tempfile

import yt_dlp


UA_MWEB = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
    "Mobile/15E148 Safari/604.1"
)


def _cookies_opts() -> dict:
    """Build cookies-related options from environment."""
    opts: dict = {}
    browser = os.environ.get("YTDLP_BROWSER", "").strip().lower()
    if browser:
        # Tuple form accepted by yt-dlp: (browser[, profile[, keyring[, container]]])
        opts["cookiesfrombrowser"] = (browser,)
        return opts
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE")
    if cookies_file and os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
    return opts


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
            "User-Agent": UA_MWEB,
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                # mweb + ios sono i client piu' robusti senza PO token
                # quando si hanno cookies; senza cookies spesso serve
                # comunque il token.
                "player_client": ["mweb", "ios"],
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

    ydl_opts.update(_cookies_opts())

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(filename)[0] + ".mp3"
            return mp3_path if os.path.exists(mp3_path) else filename
    except Exception as e:
        print(f"Errore download: {e}")
        return None
