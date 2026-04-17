"""WordPress REST client: upload media and publish posts."""
import io

import aiohttp


async def _upload_image(
    session: aiohttp.ClientSession,
    image_content: bytes,
    filename: str,
    wp_url: str,
) -> int | None:
    data = aiohttp.FormData()
    data.add_field("file", io.BytesIO(image_content), filename=filename)
    async with session.post(f"{wp_url}/wp-json/wp/v2/media", data=data) as resp:
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
    """Create a published WordPress post, optionally with a featured image."""
    wp_url = wp_url.rstrip("/")
    auth = aiohttp.BasicAuth(username, password)

    async with aiohttp.ClientSession(auth=auth) as session:
        media_id = None
        if image_content:
            media_id = await _upload_image(session, image_content, image_filename, wp_url)

        payload = {"title": title, "content": content, "status": "publish"}
        if media_id:
            payload["featured_media"] = media_id

        async with session.post(
            f"{wp_url}/wp-json/wp/v2/posts", json=payload
        ) as resp:
            if resp.status == 201:
                return await resp.json()
            print(f"Pubblicazione fallita: {resp.status} - {await resp.text()}")
            return None
