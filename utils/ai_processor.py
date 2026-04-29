"""LLM helpers: generate title and three bullet-point summary via llm_client."""
from llm_client import generate


def generate_title(text: str) -> str:
    """Generate a short, catchy Italian title for the given text."""
    try:
        return generate(
            prompt=f"Scrivi un titolo breve (max 10 parole) per questo testo:\n\n{text}",
            system="Sei un copywriter italiano. Rispondi solo con il titolo, senza virgolette.",
            temperature=0.7,
            max_tokens=50,
        )
    except Exception as e:
        print(f"Errore generate_title: {e}")
        return "Senza titolo"


def process_text(text: str) -> list[str]:
    """Return up to 3 bullet-point summary strings in Italian."""
    try:
        content = generate(
            prompt=f"Riassumi in 3 punti questo testo:\n\n{text}",
            system=(
                "Sei un assistente che riassume testi in italiano in esattamente "
                "3 punti chiave, uno per riga, senza numerazione ne elenchi puntati."
            ),
            temperature=0.5,
            max_tokens=200,
        )
        points = [p.strip(" -*\t") for p in content.splitlines() if p.strip()]
        return points[:3]
    except Exception as e:
        print(f"Errore process_text: {e}")
        return []
