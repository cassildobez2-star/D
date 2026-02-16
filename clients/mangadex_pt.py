import aiohttp
import os

from .base import BaseClient


class MangaDexPT(BaseClient):

    BASE_URL = "https://api.mangadex.org"
    COVER_URL = "https://uploads.mangadex.org/covers"
    IMAGE_SERVER = "https://uploads.mangadex.org"

    async def search(self, query: str):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/manga",
                params={
                    "title": query,
                    "availableTranslatedLanguage[]": "pt-br",
                    "limit": 5
                }
            ) as resp:
                data = await resp.json()

        results = []

        for item in data.get("data", []):
            title = list(item["attributes"]["title"].values())[0]
            manga_id = item["id"]

            results.append({
                "id": manga_id,
                "title": title
            })

        return results

    async def get_chapters(self, manga_id: str):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/chapter",
                params={
                    "manga": manga_id,
                    "translatedLanguage[]": "pt-br",
                    "order[chapter]": "desc",
                    "limit": 20
                }
            ) as resp:
                data = await resp.json()

        chapters = []

        for item in data.get("data", []):
            chapter_number = item["attributes"].get("chapter")
            chapter_id = item["id"]

            if chapter_number:
                chapters.append({
                    "id": chapter_id,
                    "name": f"Capítulo {chapter_number}"
                })

        return chapters

    async def download(self, chapter_id: str, folder: str):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/at-home/server/{chapter_id}"
            ) as resp:
                data = await resp.json()

        base_url = data["baseUrl"]
        chapter_hash = data["chapter"]["hash"]
        pages = data["chapter"]["data"]

        image_paths = []

        async with aiohttp.ClientSession() as session:
            for page in pages:
                image_url = f"{base_url}/data/{chapter_hash}/{page}"
                image_path = os.path.join(folder, page)

                async with session.get(image_url) as img_resp:
                    if img_resp.status == 200:
                        with open(image_path, "wb") as f:
                            f.write(await img_resp.read())
                        image_paths.append(image_path)

        return image_paths
