import requests


def transcribe_audio(audio_file: str, api_key: str) -> str | None:
    """Trascrive un file audio usando le API Deepgram."""
    try:
        with open(audio_file, "rb") as f:
            audio_data = f.read()

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/mpeg",
        }
        url = "https://api.deepgram.com/v1/listen?punctuate=true&language=it"
        response = requests.post(url, headers=headers, data=audio_data, timeout=120)

        if response.status_code == 200:
            return (
                response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
            )

        print(f"Deepgram error {response.status_code}: {response.text}")
        return None

    except Exception as e:
        print(f"Errore trascrizione: {e}")
        return None
