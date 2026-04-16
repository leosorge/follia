import streamlit as st
import asyncio
import nest_asyncio
nest_asyncio.apply()

from utils.downloader import download_youtube_audio
from utils.transcriber import transcribe_audio
from utils.ai_processor import generate_title, process_text
from utils.wordpress import create_post
from utils.helpers import get_youtube_thumbnail, save_to_files

st.set_page_config(
    page_title="YT → WordPress",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 YouTube → WordPress Publisher")
st.markdown("Scarica, trascrive, riassume e pubblica automaticamente su WordPress.")

# --- Sidebar: Configurazione ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    deepgram_key = st.text_input("Deepgram API Key", type="password", value="")
    openai_key   = st.text_input("OpenAI API Key",   type="password", value="")
    wp_url       = st.text_input("WordPress URL",    value="https://www.greenstart.it")
    wp_user      = st.text_input("WP Username",      value="")
    wp_password  = st.text_input("WP App Password",  type="password", value="")
    st.divider()
    st.caption("Le credenziali non vengono salvate sul server.")

# --- Input URL ---
youtube_url = st.text_input("🔗 URL del video YouTube", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Avvia Pipeline", use_container_width=True, type="primary"):
    if not youtube_url:
        st.error("Inserisci un URL YouTube valido.")
        st.stop()

    missing = [k for k, v in {
        "Deepgram Key": deepgram_key,
        "OpenAI Key":   openai_key,
        "WP URL":       wp_url,
        "WP Username":  wp_user,
        "WP Password":  wp_password,
    }.items() if not v]
    if missing:
        st.error(f"Campi mancanti nella sidebar: {', '.join(missing)}")
        st.stop()

    # Step 1 – Download
    with st.status("📥 Scaricamento audio...", expanded=True) as status:
        audio_file = download_youtube_audio(youtube_url)
        if not audio_file:
            status.update(label="❌ Download fallito", state="error")
            st.stop()
        status.update(label="✅ Audio scaricato", state="complete")

    # Step 2 – Trascrizione
    with st.status("🎙️ Trascrizione in corso...", expanded=True) as status:
        transcript = transcribe_audio(audio_file, deepgram_key)
        if not transcript:
            status.update(label="❌ Trascrizione fallita", state="error")
            st.stop()
        status.update(label="✅ Trascrizione completata", state="complete")

    st.subheader("📝 Trascrizione")
    with st.expander("Mostra testo completo"):
        st.write(transcript)

    # Step 3 – Elaborazione AI
    with st.status("🤖 Generazione sintesi...", expanded=True) as status:
        points = process_text(transcript, openai_key)
        title  = generate_title(transcript[:500], openai_key)
        if not points:
            status.update(label="❌ Elaborazione AI fallita", state="error")
            st.stop()
        status.update(label="✅ Sintesi generata", state="complete")

    st.subheader(f"📌 Titolo: {title}")
    for i, p in enumerate(points, 1):
        st.info(f"**Punto {i}:** {p}")

    # Step 4 – Thumbnail
    img_data = get_youtube_thumbnail(youtube_url)

    # Step 5 – Salvataggio locale
    save_to_files(points, title, youtube_url)

    # Step 6 – Pubblicazione WordPress
    with st.status("📤 Pubblicazione su WordPress...", expanded=True) as status:
        content = "\n\n".join(points) + f"\n\n<p>Sintesi da <a href='{youtube_url}'>video YouTube</a></p>"
        post = asyncio.run(
            create_post(title, content, img_data, "thumb.jpg", wp_url, wp_user, wp_password)
        )
        if post and post.get("id"):
            status.update(label="✅ Post pubblicato!", state="complete")
            st.success(f"🎉 Post pubblicato con ID **{post['id']}**")
            if post.get("link"):
                st.markdown(f"[🔗 Visualizza il post]({post['link']})", unsafe_allow_html=True)
        else:
            status.update(label="❌ Pubblicazione fallita", state="error")
            st.error("Errore durante la pubblicazione. Controlla le credenziali WordPress.")
