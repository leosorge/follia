"""Audio transcription via Deepgram REST API."""
import requests


def transcribe_audio(audio_file: str, api_key: str) -> str | None:
    """Transcribe an audio file with Deepgram (Italian).

    Raises RuntimeError on HTTP errors or unexpected responses so the
    caller can surface a descriptive message instead of a silent None.
    """
    with open(audio_file, "rb") as f:
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/mpeg",
        }
        url = "https://api.deepgram.com/v1/listen?punctuate=true&language=it"
        response = requests.post(url, headers=headers, data=f, timeout=300)

    if response.status_code != 200:
        body = response.text[:500]
        raise RuntimeError(f"Deepgram {response.status_code}: {body}")

    try:
        transcript = (
            response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(f"Risposta Deepgram inattesa: {response.text[:500]}") from e

    return transcript
