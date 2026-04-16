import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

st.set_page_config(page_title="Pubblica su WordPress", page_icon="🌐", layout="wide")

st.title("🌐 Pubblica su WordPress")
st.caption("Carica immagine e pubblica l'articolo generato · FT-CS © Leo Sorge 2025")

FIRMA = "*Testo realizzato automaticamente con GenAIs pilotate dal software FT-CS © Leo Sorge 2025 e rieditato dalla redazione*"

# ── Sidebar: credenziali WP ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ WordPress")
    wp_url = st.text_input("URL sito", placeholder="https://miosito.wordpress.com")
    wp_user = st.text_input("Username / Email")
    wp_pass = st.text_input("Application Password", type="password",
                            help="Genera una Application Password da WordPress → Utenti → Profilo")
    wp_category = st.text_input("Categoria", value="News")
    st.markdown("---")
    st.info("Usa le **Application Password** di WordPress, non la password di accesso.")

# ── Funzioni WordPress ────────────────────────────────────────────────────────

def carica_immagine(wp_url: str, auth: HTTPBasicAuth, file) -> int | None:
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f'attachment; filename="{file.name}"'}
    try:
        resp = requests.post(
            endpoint,
            auth=auth,
            headers=headers,
            data=file.read(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("id")
    except requests.exceptions.HTTPError:
        st.error(f"Errore upload immagine: {resp.status_code} — {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Errore di rete: {e}")
    return None


def crea_post(
    wp_url: str,
    auth: HTTPBasicAuth,
    titolo: str,
    contenuto: str,
    image_id: int | None,
    categoria: str,
) -> int | None:
    endpoint = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    data: dict = {
        "title": titolo,
        "content": contenuto,
        "status": "publish",
    }
    if image_id:
        data["featured_media"] = image_id
    # Nota: le categorie richiedono l'ID numerico. Se si vuole usare il nome
    # bisogna prima fare una GET su /wp-json/wp/v2/categories?search=<nome>
    try:
        resp = requests.post(endpoint, auth=auth, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json().get("id")
    except requests.exceptions.HTTPError:
        st.error(f"Errore creazione post: {resp.status_code} — {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Errore di rete: {e}")
    return None


# ── Form articolo ─────────────────────────────────────────────────────────────
st.subheader("✍️ Componi l'articolo")

col1, col2 = st.columns(2)
with col1:
    titolo = st.text_input("Titolo")
with col2:
    titoletto = st.text_input("Titoletto (sottotitolo intermedio)")

parte1 = st.text_area("Parte 1", height=150)
parte2 = st.text_area("Parte 2", height=150)
immagine = st.file_uploader("Immagine in evidenza", type=["jpg", "jpeg", "png", "webp"])

# Anteprima
if titolo or parte1 or parte2:
    with st.expander("👁 Anteprima articolo", expanded=False):
        if titolo:
            st.markdown(f"# {titolo}")
        if parte1:
            st.write(parte1)
        if titoletto:
            st.markdown(f"### {titoletto}")
        if parte2:
            st.write(parte2)
        st.markdown(FIRMA)

st.markdown("---")
pubblica = st.button(
    "🚀 Pubblica su WordPress",
    type="primary",
    disabled=not (wp_url and wp_user and wp_pass and titolo and (parte1 or parte2)),
)

# ── Pubblicazione ─────────────────────────────────────────────────────────────
if pubblica:
    auth = HTTPBasicAuth(wp_user, wp_pass)
    image_id = None

    if immagine:
        with st.spinner("Caricamento immagine..."):
            image_id = carica_immagine(wp_url, auth, immagine)
        if image_id:
            st.success(f"Immagine caricata (ID: {image_id})")

    contenuto_html = (
        f"<p>{parte1}</p>\n"
        f"<h3>{titoletto}</h3>\n"
        f"<p>{parte2}</p>\n"
        f"<p><em>{FIRMA.strip('*')}</em></p>"
    )

    with st.spinner("Pubblicazione articolo..."):
        post_id = crea_post(wp_url, auth, titolo, contenuto_html, image_id, wp_category)

    if post_id:
        st.success(f"✅ Articolo pubblicato con ID: {post_id}")
        st.markdown(f"[Vai al post]({wp_url.rstrip('/')}/?p={post_id})")
