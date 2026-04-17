"""Audio transcription via Deepgram REST API."""
import requests


def transcribe_audio(audio_file: str, api_key: str) -> str | None:
    """Transcribe an audio file with Deepgram (Italian)."""
    try:
        with open(audio_file, "rb") as f:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "audio/mpeg",
            }
            url = "https://api.deepgram.com/v1/listen?punctuate=true&language=it"
            # Stream the file instead of loading it fully in memory
            response = requests.post(url, headers=headers, data=f, timeout=300)

        if response.status_code == 200:
            return (
                response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
            )

        print(f"Deepgram error {response.status_code}: {response.text}")
        return None

    except Exception as e:
        print(f"Errore trascrizione: {e}")
        return None
