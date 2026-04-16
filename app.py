import streamlit as st
import requests

# ── Configurazione pagina ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Follia on Regolo",
    page_icon="📰",
    layout="wide",
)

st.title("📰 Follia on Regolo")
st.caption("Sintesi automatica di testi tramite Regolo.ai · FT-CS © Leo Sorge 2025")

FIRMA = "*Testo realizzato automaticamente con GenAIs pilotate dal software FT-CS © Leo Sorge 2025 e rieditato dalla redazione*"

MODELLI = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.2",
]

# ── Funzioni API ─────────────────────────────────────────────────────────────

def chiama_regolo(token: str, model: str, prompt: str) -> str | None:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = requests.post(
            "https://api.regolo.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        st.error(f"Errore HTTP {resp.status_code}: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Errore di rete: {e}")
    return None


def genera_sintesi(token: str, model: str, testo: str) -> str | None:
    prompt = (
        "Sintetizza in 400 parole, senza punti elenco e senza conclusioni, "
        "semplificando il linguaggio ma mantenendo le informazioni, "
        "in particolare quelle numeriche, del seguente testo:\n\n" + testo
    )
    return chiama_regolo(token, model, prompt)


def genera_titolo(token: str, model: str, testo: str) -> str | None:
    prompt = (
        "Genera un titolo conciso e informativo (max 10 parole), che inizia con il nome "
        "dell'azienda citata, senza virgolette e con le maiuscole all'europea "
        "(non tutte le parole con la maiuscola), partendo dal seguente testo:\n\n" + testo
    )
    return chiama_regolo(token, model, prompt)


def genera_testo_processato(token: str, model: str, testo: str) -> str | None:
    prompt = (
        "Leggi attentamente il seguente testo:\n\n"
        + testo
        + "\n\nRiscrivilo in modo più chiaro e giornalistico, mantenendo tutti i dati numerici. "
        "Dividilo in due parti separate da un titoletto intermedio. "
        "Non aggiungere conclusioni né punti elenco."
    )
    return chiama_regolo(token, model, prompt)


# ── Sidebar: configurazione ───────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurazione")
    token = st.text_input("Token Regolo.ai", type="password", placeholder="rai_...")
    model = st.selectbox("Modello", MODELLI)
    st.markdown("---")
    st.markdown("[Ottieni un token Regolo.ai](https://regolo.ai)")
    st.markdown("**Modalità**")
    modalita = st.radio("", ["Solo sintesi", "Sintesi + titolo + testo completo"])

# ── Input testo ───────────────────────────────────────────────────────────────
st.subheader("📝 Testo da elaborare")
testo_input = st.text_area("Incolla il testo da sintetizzare", height=250)

col1, col2 = st.columns([1, 5])
with col1:
    avvia = st.button("▶ Elabora", type="primary", disabled=not token or not testo_input)

# ── Elaborazione ──────────────────────────────────────────────────────────────
if avvia:
    if not token:
        st.warning("Inserisci il token Regolo.ai nella barra laterale.")
    elif not testo_input.strip():
        st.warning("Inserisci un testo da elaborare.")
    else:
        with st.spinner("Generazione sintesi in corso..."):
            sintesi = genera_sintesi(token, model, testo_input)

        if sintesi:
            st.subheader("📄 Sintesi")
            st.write(sintesi)
            st.markdown("---")

            if modalita == "Sintesi + titolo + testo completo":
                with st.spinner("Generazione titolo..."):
                    titolo = genera_titolo(token, model, sintesi)
                with st.spinner("Generazione testo processato..."):
                    testo_proc = genera_testo_processato(token, model, sintesi)

                if titolo:
                    st.subheader("🏷️ Titolo generato")
                    st.markdown(f"### {titolo.strip()}")

                if testo_proc:
                    st.subheader("📰 Testo completo")
                    st.write(testo_proc)
                    st.markdown(FIRMA)

                # Output copia-incolla
                st.markdown("---")
                st.subheader("📋 Output finale (copia-incolla)")
                output_finale = f"**{titolo.strip() if titolo else ''}**\n\n{testo_proc or sintesi}\n\n{FIRMA}"
                st.text_area("", value=output_finale, height=300)
            else:
                st.markdown(FIRMA)
