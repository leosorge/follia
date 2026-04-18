"""Download audio from a YouTube URL using yt-dlp.

YouTube blocca spesso i download con HTTP 403 o "Sign in to confirm you're
not a bot". Le contromisure in ordine di efficacia:

1. Cookies come contenuto in secret (ideale per Streamlit Cloud): incollare
   il contenuto completo di un cookies.txt (formato Netscape) nel secret
   YTDLP_COOKIES_CONTENT. A runtime lo scriviamo in un file temporaneo e
   lo passiamo a yt-dlp.

2. Cookies da file locale: impostare YTDLP_COOKIES_FILE al path di un
   cookies.txt esistente.

3. Cookies dal browser (solo uso locale, non su server senza browser):
   impostare YTDLP_BROWSER (chrome, firefox, edge, brave, chromium,
   safari, opera, vivaldi). yt-dlp legge direttamente i cookies dal
   profilo attivo del browser.

4. Fallback: senza cookies proviamo con client mweb e ios, ma molti
   video privati/age-gated falliranno.

Come esportare cookies.txt (una volta, dal tuo PC):
- Installa l'estensione Chrome/Firefox "Get cookies.txt LOCALLY"
- Vai su https://www.youtube.com (loggato)
- Clicca l'estensione -> Export -> salva cookies.txt
- Copia TUTTO il contenuto del file nel secret YTDLP_COOKIES_CONTENT
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
    """Build cookies-related options from environment variables."""
    opts: dict = {}

    # 1. Cookies content as secret (Streamlit Cloud friendly)
    content = os.environ.get("YTDLP_COOKIES_CONTENT")
    if content and content.strip():
        # Write to a stable temp file (reuse across calls in the same process)
        tmp_path = os.path.join(tempfile.gettempdir(), "yt2wp_cookies.txt")
        try:
            with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            opts["cookiefile"] = tmp_path
            return opts
        except Exception as e:
            print(f"Impossibile scrivere cookies temporanei: {e}")

    # 2. Cookies file path
    cookies_file = os.environ.get("YTDLP_COOKIES_FILE")
    if cookies_file and os.path.isfile(cookies_file):
        opts["cookiefile"] = cookies_file
        return opts

    # 3. Cookies from installed browser (local dev only)
    browser = os.environ.get("YTDLP_BROWSER", "").strip().lower()
    if browser:
        opts["cookiesfrombrowser"] = (browser,)

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
