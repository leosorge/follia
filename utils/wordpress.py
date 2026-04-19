"""WordPress REST client: upload media and publish posts."""
import io
import socket

import aiohttp


_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 follia-pipeline"
)


async def _upload_image(
    session: aiohttp.ClientSession,
    image_content: bytes,
    filename: str,
    wp_url: str,
) -> int | None:
    data = aiohttp.FormData()
    data.add_field("file", io.BytesIO(image_content), filename=filename)
    async with session.post(f"{wp_url}/?rest_route=/wp/v2/media", data=data) as resp:
        if resp.status == 201:
            return (await resp.json()).get("id")
        print(f"Upload immagine fallito: {resp.status} - {await resp.text()}")
        return None


async def create_post(
    title: str,
    content: str,
    image_content: bytes | None,
    image_filename: str,
    wp_url: str,
    username: str,
    password: str,
) -> dict | None:
    """Create a published WordPress post, optionally with a featured image.

    - Forza IPv4 (molti host italiani non rispondono su IPv6 e aiohttp
      non fa fallback rapido, causando ConnectionTimeoutError).
    - Usa User-Agent realistico (alcuni WAF bloccano UA python/aiohttp).
    - Fa un preflight GET sul REST per fallire subito con messaggio
      chiaro se l'host non risponde da Streamlit Cloud.
    """
    wp_url = wp_url.rstrip("/")
    auth = aiohttp.BasicAuth(username, password)
    timeout = aiohttp.ClientTimeout(connect=15, total=180)
    headers = {"User-Agent": _USER_AGENT}
    connector = aiohttp.TCPConnector(family=socket.AF_INET)

    async with aiohttp.ClientSession(
        auth=auth,
        headers=headers,
        timeout=timeout,
        connector=connector,
    ) as session:
        # Preflight: verifica che l'host sia raggiungibile dal runner.
        try:
            async with session.get(f"{wp_url}/?rest_route=/") as preflight:
                if preflight.status >= 500:
                    raise RuntimeError(
                        f"WordPress REST irraggiungibile: HTTP {preflight.status}."
                    )
        except (aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError) as e:
            raise RuntimeError(
                f"Impossibile connettersi a {wp_url} dal server Streamlit: {e}. "
                "Probabile geoblocking o firewall lato hosting."
            ) from e

        media_id = None
        if image_content:
            media_id = await _upload_image(session, image_content, image_filename, wp_url)

        payload = {"title": title, "content": content, "status": "publish"}
        if media_id:
            payload["featured_media"] = media_id

        async with session.post(
            f"{wp_url}/?rest_route=/wp/v2/posts", json=payload
        ) as resp:
            if resp.status == 201:
                return await resp.json()
            print(f"Pubblicazione fallita: {resp.status} - {await resp.text()}")
            return None
