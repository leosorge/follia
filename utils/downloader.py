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
import re
import tempfile
import textwrap

import yt_dlp


def _normalize_cookies_content(raw: str) -> str:
    """Normalize a cookies.txt pasted in Streamlit secrets.

    Streamlit TOML triple-quoted strings often keep leading whitespace on
    each line. yt-dlp expects strict Netscape format:
    - first non-blank line must start with "# Netscape HTTP Cookie File"
    - fields must be separated by TAB (not spaces).
    """
    # Drop BOM and normalize line endings.
    text = raw.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    # Remove any common leading indentation from the whole block.
    text = textwrap.dedent(text)
    lines_out = []
    for line in text.split("\n"):
        # Strip only leading/trailing whitespace from comment/blank lines.
        # Data lines must keep their internal TABs intact.
        stripped = line.strip()
        if not stripped:
            lines_out.append("")
            continue
        if stripped.startswith("#"):
            lines_out.append(stripped)
            continue
        # Data line: if separators are spaces, convert runs of whitespace
        # to single TABs (Netscape uses TAB as delimiter).
        if "\t" not in line:
            parts = re.split(r"\s+", stripped)
            if len(parts) >= 7:
                lines_out.append("\t".join(parts[:6]) + "\t" + " ".join(parts[6:]))
            else:
                lines_out.append(stripped)
        else:
            lines_out.append(line.lstrip())
    # Ensure header is present as very first line.
    header = "# Netscape HTTP Cookie File"
    cleaned = "\n".join(lines_out).lstrip("\n")
    if not cleaned.startswith(header):
        cleaned = header + "\n" + cleaned
    if not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned


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
        # Normalize: dedent, fix line endings, ensure Netscape header + TABs.
        normalized = _normalize_cookies_content(content)
        tmp_path = os.path.join(tempfile.gettempdir(), "yt2wp_cookies.txt")
        try:
            with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(normalized)
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
        # Node.js come runtime JS esterno per risolvere la n-challenge di
        # YouTube. yt-dlp accetta deno/node/bun/quickjs. Su Streamlit Cloud
        # installiamo nodejs via packages.txt. Combinato con yt-dlp-ejs
        # (in requirements.txt) permette di decifrare le signature.
        "js_runtimes": {"node": {}},
        "extractor_args": {
            "youtube": {
                # Ordine basato su yt-dlp INNERTUBE_CLIENTS (2026).
                # Privilegia i client che NON richiedono GVS PO Token:
                # - tv: GVS PO Token NON richiesto, supporta cookies,
                #   no auth. Primo tentativo.
                # - tv_downgraded: GVS PO Token NON richiesto, supporta
                #   cookies (richiede auth, quindi servono cookies).
                # - web_embedded: GVS PO Token NON richiesto, supporta
                #   cookies. Fallback sicuro.
                # - web_safari / mweb: richiedono GVS PO Token per
                #   https, ma non per HLS; ultimo fallback.
                "player_client": ["tv", "tv_downgraded", "web_embedded", "web_safari", "mweb"],
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
