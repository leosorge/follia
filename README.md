# 🎬 YouTube → WordPress Publisher

Pipeline automatica che:
1. **Scarica** l'audio da un video YouTube (yt-dlp)
2. **Trascrive** l'audio in italiano (Deepgram)
3. **Riassume** il testo in 3 punti (Regolo - Llama 3.3)
4. **Pubblica** il post con thumbnail su WordPress (REST API)

## 📁 Struttura del progetto

```
follia/
├── app.py                        # Entry point Streamlit
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example      # Template credenziali
├── utils/
│   ├── __init__.py
│   ├── downloader.py             # Download audio YouTube
│   ├── transcriber.py            # Trascrizione Deepgram
│   ├── ai_processor.py           # Titolo + sintesi Regolo
│   ├── wordpress.py              # Upload media + post WP
│   └── helpers.py                # Thumbnail + salvataggio file
├── pages/
│   └── 1_Pubblica_WordPress.py   # Pagina Streamlit aggiuntiva
└── output/                       # File generati (gitignored)
```

## 🚀 Installazione locale

```bash
git clone https://github.com/leosorge/follia.git
cd follia
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

| Variabile         | Dove ottenerla                 |
|-------------------|--------------------------------|
| DEEPGRAM_API_KEY  | console.deepgram.com           |
| REGOLO_API_KEY    | regolo.ai                      |
| WP_URL            | URL del tuo sito WordPress     |
| WP_USERNAME       | Username amministratore WP     |
| WP_APP_PASSWORD   | App Password (non la password normale) |

> 💡 Per generare un'App Password WordPress: **Utenti → Profilo → Password applicazione**

## ⚠️ Note di sicurezza

- **Non committare mai `secrets.toml`** su Git (già nel `.gitignore`)
- Le credenziali inserite nella sidebar non vengono salvate sul server
- Usa sempre le **App Password** di WordPress, non la password principale
