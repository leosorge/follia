"""OpenAI helpers: generate title and three bullet-point summary."""
from openai import OpenAI

MODEL = "gpt-3.5-turbo"


def _client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def generate_title(text: str, api_key: str) -> str:
    """Generate a short, catchy Italian title for the given text."""
    try:
        resp = _client(api_key).chat.completions.create(
            model=MODEL,
            temperature=0.7,
            messages=[
                {"role": "system", "content": "Sei un copywriter italiano. Rispondi solo con il titolo, senza virgolette."},
                {"role": "user", "content": f"Scrivi un titolo breve (max 10 parole) per questo testo:\n\n{text}"},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Errore generate_title: {e}")
        return "Senza titolo"


def process_text(text: str, api_key: str) -> list[str]:
    """Return up to 3 bullet-point summary strings in Italian."""
    try:
        resp = _client(api_key).chat.completions.create(
            model=MODEL,
            temperature=0.5,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei un assistente che riassume testi in italiano in esattamente "
                        "3 punti chiave, uno per riga, senza numerazione n\u00e9 elenchi puntati."
                    ),
                },
                {"role": "user", "content": f"Riassumi in 3 punti questo testo:\n\n{text}"},
            ],
        )
        content = resp.choices[0].message.content.strip()
        points = [p.strip(" -*\t") for p in content.splitlines() if p.strip()]
        return points[:3]
    except Exception as e:
        print(f"Errore process_text: {e}")
        return []
