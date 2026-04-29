"""YouTube -> WordPress publishing pipeline (Streamlit entry point)."""
import asyncio
import os

import streamlit as st
from llm_client import render_provider_selector

from utils.ai_processor import generate_title, process_text
from utils.downloader import download_youtube_audio
from utils.helpers import get_youtube_thumbnail, save_to_files
from utils.transcriber import transcribe_audio
from utils.wordpress import create_post

# Bridge Streamlit secrets -> env vars per yt-dlp (cookies YouTube).
for _key in ("YTDLP_COOKIES_CONTENT", "YTDLP_COOKIES_FILE", "YTDLP_BROWSER"):
    try:
        _val = st.secrets.get(_key)  # type: ignore[attr-defined]
    except Exception:
        _val = None
    if _val and not os.environ.get(_key):
        os.environ[_key] = str(_val)

st.set_page_config(page_title="YT \u2192 WordPress", page_icon="\U0001F3AC", layout="centered")
st.title("\U0001F3AC YouTube \u2192 WordPress Publisher")
st.markdown("Scarica, trascrive, riassume e pubblica automaticamente su WordPress.")

with st.sidebar:
    st.header("\u2699\uFE0F Configurazione")
    render_provider_selector()
    deepgram_key = st.text_input("Deepgram API Key", type="password", value="")
    wp_url = st.text_input("WordPress URL", value="", placeholder="https://www.tuosito.it")
    wp_user = st.text_input("WP Username", value="")
    wp_password = st.text_input("WP App Password", type="password", value="")
    st.divider()
    st.caption("Le credenziali non vengono salvate sul server.")

youtube_url = st.text_input("\U0001F517 URL del video YouTube", placeholder="https://www.youtube.com/watch?v=...")


def _bullets_to_html(points: list[str], source_url: str) -> str:
    """Render bullet list as HTML ready for WordPress post body."""
    items = "".join(f"<li>{p}</li>" for p in points if p.strip())
    return (
        f"<ul>{items}</ul>"
        f"<p>Sintesi dal <a href='{source_url}' target='_blank' rel='noopener'>video</a>.</p>"
    )


if st.button("\U0001F680 Avvia Pipeline", use_container_width=True, type="primary"):
    if not youtube_url:
        st.error("Inserisci un URL YouTube valido.")
        st.stop()
    missing = [k for k, v in {
        "Deepgram Key": deepgram_key,
        "WP URL": wp_url,
        "WP Username": wp_user,
        "WP Password": wp_password,
    }.items() if not v]
    if missing:
        st.error(f"Campi mancanti nella sidebar: {', '.join(missing)}")
        st.stop()

    with st.status("Pipeline in corso...", expanded=True) as status:
        try:
            st.write("\U0001F4E5 Scarico audio da YouTube...")
            audio_path = download_youtube_audio(youtube_url)
            if not audio_path or not os.path.exists(audio_path):
                st.error("Download fallito: file audio non disponibile.")
                st.stop()

            st.write("\U0001F5BC\uFE0F Ottengo la miniatura...")
            thumb_bytes = get_youtube_thumbnail(youtube_url)

            st.write("\U0001F4DD Trascrivo l'audio (Deepgram)...")
            audio_size = os.path.getsize(audio_path)
            st.caption(f"File audio: {os.path.basename(audio_path)} — {audio_size/1024:.0f} KB")
            if audio_size < 1024:
                st.error(f"File audio troppo piccolo ({audio_size} bytes). Download probabilmente fallito.")
                st.stop()
            transcript = transcribe_audio(audio_path, deepgram_key)
            if not transcript:
                st.error("Trascrizione vuota. Interrompo.")
                st.stop()

            st.write("\U0001F9E0 Riassumo il testo (LLM)...")
            points = process_text(transcript)
            if not points:
                st.warning("Sintesi non disponibile dal modello: uso contenuto di default.")
                points = ["paragrafo 1", "paragrafo 2", "paragrafo 3"]

            st.write("\u270D\uFE0F Genero il titolo...")
            title = generate_title(transcript[:1500])
            if not title:
                st.warning("Titolo non disponibile dal modello: uso titolo di default.")
                title = "Titolo 1"

            st.write("\U0001F4BE Salvo file locali...")
            save_to_files(points, title, youtube_url)

            st.write("\U0001F4E4 Pubblico su WordPress...")
            content_html = _bullets_to_html(points, youtube_url)
            post = asyncio.run(
                create_post(
                    title=title,
                    content=content_html,
                    image_content=thumb_bytes,
                    image_filename="thumbnail.jpg",
                    wp_url=wp_url,
                    username=wp_user,
                    password=wp_password,
                )
            )
            if not post:
                st.error("Pubblicazione WordPress fallita. Controlla i log.")
                st.stop()
            post_url = post.get("link") or post.get("guid", {}).get("rendered", "")

            status.update(label="\u2705 Pipeline completata!", state="complete")
            st.success(f"Articolo pubblicato: {post_url}")
        except Exception as e:
            status.update(label="\u274C Errore", state="error")
            st.exception(e)
