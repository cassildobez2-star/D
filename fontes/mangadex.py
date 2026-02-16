import aiohttp
import os
from pathlib import Path
from zipfile import ZipFile

class MangaDexClient:
    name = "MangaDex"
    base_url = "https://api.mangadex.org"
    cover_url = "https://uploads.mangadex.org"

    # ==========================
    # 🔎 BUSCAR MANGÁ
    # ==========================
    async def search(self, query: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/manga",
                params={
                    "title": query,
                    "limit": 10,
                    "availableTranslatedLanguage[]": "pt-br"
                }
            ) as r:

                data = await r.json()

        results = []

        for item in data.get("data", []):
            title = item["attributes"]["title"]
            name = title.get("pt-br") or list(title.values())[0]

            results.append({
                "id": item["id"],
                "name": name
            })

        return results

    # ==========================
    # 📖 CAPÍTULOS
    # ==========================
    async def get_chapters(self, manga):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/chapter",
                params={
                    "manga": manga["id"],
                    "limit": 500,
                    "translatedLanguage[]": "pt-br",
                    "order[chapter]": "asc"
                }
            ) as r:

                data = await r.json()

        chapters = []

        for item in data.get("data", []):
            attr = item["attributes"]
            chapter_num = attr.get("chapter")

            if chapter_num is None:
                continue

            chapters.append({
                "id": item["id"],
                "name": f"Capítulo {chapter_num}",
                "chapter": float(chapter_num),
                "manga": manga
            })

        return chapters

    # ==========================
    # 📥 DOWNLOAD + CBZ
    # ==========================
    async def download_chapter(self, chapter):
        async with aiohttp.ClientSession() as session:

            # pegar servidor de imagem
            async with session.get(
                f"{self.base_url}/at-home/server/{chapter['id']}"
            ) as r:

                data = await r.json()

            base = data["baseUrl"]
            chapter_data = data["chapter"]
            hash_code = chapter_data["hash"]
            pages = chapter_data["data"]

            folder = Path("cache") / chapter["name"].replace(" ", "_")
            folder.mkdir(parents=True, exist_ok=True)

            image_paths = []

            for i, page in enumerate(pages):
                img_url = f"{base}/data/{hash_code}/{page}"

                async with session.get(img_url) as img_resp:
                    img_bytes = await img_resp.read()

                ext = page.split(".")[-1]
                img_path = folder / f"{i+1}.{ext}"

                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                image_paths.append(img_path)

        # Criar CBZ
        cbz_path = folder.with_suffix(".cbz")

        with ZipFile(cbz_path, "w") as zipf:
            for img in image_paths:
                zipf.write(img, img.name)

        # 🔥 LIMPEZA IMEDIATA (Railway safe)
        for img in image_paths:
            os.remove(img)

        folder.rmdir()

        return cbz_path
