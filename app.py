"""YouTube -> WordPress publishing pipeline (Streamlit entry point)."""
import asyncio
import os

import nest_asyncio
import streamlit as st

from utils.ai_processor import generate_title, process_text
from utils.downloader import download_youtube_audio
from utils.helpers import get_youtube_thumbnail, save_to_files
from utils.transcriber import transcribe_audio
from utils.wordpress import create_post

nest_asyncio.apply()

st.set_page_config(
    page_title="YT \u2192 WordPress",
    page_icon="\U0001F3AC",
    layout="centered",
)

st.title("\U0001F3AC YouTube \u2192 WordPress Publisher")
st.markdown("Scarica, trascrive, riassume e pubblica automaticamente su WordPress.")

# --- Sidebar: configurazione ---
with st.sidebar:
    st.header("\u2699\ufe0f Configurazione")
    deepgram_key = st.text_input("Deepgram API Key", type="password", value="")
    openai_key = st.text_input("OpenAI API Key", type="password", value="")
    wp_url = st.text_input("WordPress URL", value="", placeholder="https://www.tuosito.it")
    wp_user = st.text_input("WP Username", value="")
    wp_password = st.text_input("WP App Password", type="password", value="")
    st.divider()
    st.caption("Le credenziali non vengono salvate sul server.")

youtube_url = st.text_input("\U0001F517 URL del video YouTube", placeholder="https://www.youtube.com/watch?v=...")

if st.button("\U0001F680 Avvia Pipeline", use_container_width=True, type="primary"):
    if not youtube_url:
        st.error("Inserisci un URL YouTube valido.")
        st.stop()

    missing = [k for k, v in {
        "Deepgram Key": deepgram_key,
        "OpenAI Key": openai_key,
        "WP URL": wp_url,
        "WP Username": wp_user,
        "WP Password": wp_password,
    }.items() if not v]
    if missing:
        st.error(f"Campi mancanti nella sidebar: {', '.join(missing)}")
        st.stop()

    # Step 1 - Download
    with st.status("\U0001F4E5 Scaricamento audio...", expanded=True) as status:
        audio_file = download_youtube_audio(youtube_url)
        if not audio_file:
            status.update(label="\u274C Download fallito", state="error")
            st.stop()
        status.update(label="\u2705 Audio scaricato", state="complete")

    try:
        # Step 2 - Trascrizione
        with st.status("\U0001F399\ufe0f Trascrizione in corso...", expanded=True) as status:
            transcript = transcribe_audio(audio_file, deepgram_key)
            if not transcript:
                status.update(label="\u274C Trascrizione fallita", state="error")
                st.stop()
            status.update(label="\u2705 Trascrizione completata", state="complete")

        st.subheader("\U0001F4DD Trascrizione")
        with st.expander("Mostra testo completo"):
            st.write(transcript)

        # Step 3 - Elaborazione AI
        with st.status("\U0001F916 Generazione sintesi...", expanded=True) as status:
            points = process_text(transcript, openai_key)
            title = generate_title(transcript[:1500], openai_key)
            if not points:
                status.update(label="\u274C Elaborazione AI fallita", state="error")
                st.stop()
            status.update(label="\u2705 Sintesi generata", state="complete")

        st.subheader(f"\U0001F4CC Titolo: {title}")
        for i, p in enumerate(points, 1):
            st.info(f"**Punto {i}:** {p}")

        # Step 4 - Thumbnail
        img_data = get_youtube_thumbnail(youtube_url)

        # Step 5 - Salvataggio locale
        save_to_files(points, title, youtube_url)

        # Step 6 - Pubblicazione WordPress
        with st.status("\U0001F4E4 Pubblicazione su WordPress...", expanded=True) as status:
            content = "\n\n".join(points) + f"\n\n<p>Sintesi da <a href='{youtube_url}'>video YouTube</a></p>"
            post = asyncio.run(
                create_post(title, content, img_data, "thumb.jpg", wp_url, wp_user, wp_password)
            )
            if post and post.get("id"):
                status.update(label="\u2705 Post pubblicato!", state="complete")
                st.success(f"\U0001F389 Post pubblicato con ID **{post['id']}**")
                if post.get("link"):
                    st.markdown(f"[\U0001F517 Visualizza il post]({post['link']})")
            else:
                status.update(label="\u274C Pubblicazione fallita", state="error")
                st.error("Errore durante la pubblicazione. Controlla le credenziali WordPress.")
    finally:
        # Pulizia file audio temporaneo
        try:
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)
        except OSError:
            pass
