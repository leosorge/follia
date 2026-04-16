# 🎬 YouTube → WordPress Publisher

Pipeline automatica che:
1. **Scarica** l'audio da un video YouTube (yt-dlp)
2. **Trascrive** l'audio in italiano (Deepgram)
3. **Riassume** il testo in 3 punti (OpenAI GPT-3.5)
4. **Pubblica** il post con thumbnail su WordPress (REST API)

## 📁 Struttura del progetto

```
yt2wp/
├── app.py                        # Entry point Streamlit
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example      # Template credenziali
├── utils/
│   ├── __init__.py
│   ├── downloader.py             # Download audio YouTube
│   ├── transcriber.py            # Trascrizione Deepgram
│   ├── ai_processor.py           # Titolo + sintesi OpenAI
│   ├── wordpress.py              # Upload media + post WP
│   └── helpers.py                # Thumbnail + salvataggio file
└── output/                       # File generati (gitignored)
    ├── titolo.txt
    └── sintesi.txt
```

## 🚀 Installazione locale

```bash
git clone https://github.com/tuo-utente/yt2wp.git
cd yt2wp
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Modifica secrets.toml con le tue credenziali
streamlit run app.py
```

## ☁️ Deploy su Streamlit Cloud

1. Fai il fork del repository su GitHub
2. Vai su [share.streamlit.io](https://share.streamlit.io) e connetti il repo
3. Nella sezione **Secrets**, aggiungi le variabili dal file `secrets.toml.example`
4. Clicca **Deploy**

## 🔑 Credenziali necessarie

| Variabile | Dove ottenerla |
|-----------|---------------|
| `DEEPGRAM_API_KEY` | [console.deepgram.com](https://console.deepgram.com) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| `WP_URL` | URL del tuo sito WordPress |
| `WP_USERNAME` | Username amministratore WP |
| `WP_PASSWORD` | **App Password** (non la password normale) |

> 💡 Per generare un'App Password WordPress: *Utenti → Profilo → Password applicazione*

## ⚠️ Note di sicurezza

- Non committare mai `secrets.toml` su Git (già nel `.gitignore`)
- Le credenziali inserite nella sidebar **non vengono salvate** sul server
- Usa sempre le **App Password** di WordPress, non la password principale
