"""Standalone page: publish a manually-written post on WordPress."""
import asyncio

import streamlit as st

from utils.wordpress import create_post
from utils.helpers import get_youtube_thumbnail

st.set_page_config(page_title="Pubblica su WordPress", page_icon="\U0001F4E4", layout="centered")

st.title("\U0001F4E4 Pubblica su WordPress")
st.markdown("Scrivi titolo e contenuto, poi pubblica direttamente sul tuo sito WordPress.")

with st.sidebar:
    st.header("\u2699\ufe0f Credenziali")
    wp_url = st.text_input("WordPress URL", value="", placeholder="https://www.tuosito.it")
    wp_user = st.text_input("WP Username")
    wp_password = st.text_input("WP App Password", type="password")
    st.caption("Non vengono salvate sul server.")

title = st.text_input("Titolo")
content = st.text_area("Contenuto (HTML consentito)", height=240)

st.divider()

thumb_source = st.radio("Thumbnail", ["Nessuna", "Da URL YouTube", "Upload manuale"], horizontal=True)

image_bytes: bytes | None = None
image_filename = "thumb.jpg"

if thumb_source == "Da URL YouTube":
    yt_url = st.text_input("URL YouTube per la thumbnail")
    if yt_url:
        image_bytes = get_youtube_thumbnail(yt_url)
        if image_bytes:
            st.image(image_bytes, width=300)
        else:
            st.warning("Impossibile recuperare la thumbnail.")
elif thumb_source == "Upload manuale":
    upload = st.file_uploader("Carica un'immagine", type=["jpg", "jpeg", "png"])
    if upload is not None:
        image_bytes = upload.read()
        image_filename = upload.name
        st.image(image_bytes, width=300)

if st.button("\U0001F680 Pubblica", use_container_width=True, type="primary"):
    missing = [k for k, v in {"URL": wp_url, "User": wp_user, "Password": wp_password, "Titolo": title, "Contenuto": content}.items() if not v]
    if missing:
        st.error(f"Campi mancanti: {', '.join(missing)}")
        st.stop()

    with st.status("Pubblicazione in corso...", expanded=True) as status:
        post = asyncio.run(create_post(title, content, image_bytes, image_filename, wp_url, wp_user, wp_password))
        if post and post.get("id"):
            status.update(label="Post pubblicato", state="complete")
            st.success(f"\U0001F389 Post pubblicato con ID {post['id']}")
            if post.get("link"):
                st.markdown(f"[Visualizza il post]({post['link']})")
        else:
            status.update(label="Pubblicazione fallita", state="error")
            st.error("Errore durante la pubblicazione. Controlla le credenziali WordPress.")
