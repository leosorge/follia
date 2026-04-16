import io
import aiohttp


async def upload_image(
    image_content: bytes,
    filename: str,
    wp_url: str,
    username: str,
    password: str,
) -> int | None:
    """Carica un'immagine sulla libreria media di WordPress."""
    auth = aiohttp.BasicAuth(username, password)
    data = aiohttp.FormData()
    data.add_field("file", io.BytesIO(image_content), filename=filename)

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{wp_url}/wp-json/wp/v2/media", auth=auth, data=data
        ) as resp:
            if resp.status == 201:
                return (await resp.json()).get("id")
            print(f"Upload immagine fallito: {resp.status} – {await resp.text()}")
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
    """Crea e pubblica un post su WordPress."""
    auth = aiohttp.BasicAuth(username, password)

    media_id = None
    if image_content:
        media_id = await upload_image(image_content, image_filename, wp_url, username, password)

    payload = {"title": title, "content": content, "status": "publish"}
    if media_id:
        payload["featured_media"] = media_id

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{wp_url}/wp-json/wp/v2/posts", auth=auth, json=payload
        ) as resp:
            if resp.status == 201:
                return await resp.json()
            print(f"Pubblicazione fallita: {resp.status} – {await resp.text()}")
    return None
