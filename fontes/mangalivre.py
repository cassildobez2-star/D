import os
import cloudscraper
from bs4 import BeautifulSoup
from pathlib import Path
from zipfile import ZipFile


class MangaLivreClient:
    name = "MangaLivre"
    base_url = "https://mangalivre.tv"

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    # ==============================
    # 🔎 BUSCA (Cloudflare bypass)
    # ==============================
    async def search(self, query: str):
        try:
            url = f"{self.base_url}/?s={query}&post_type=wp-manga"
            r = self.scraper.get(url, timeout=20)

            soup = BeautifulSoup(r.text, "lxml")

            mangas = []
            for a in soup.select(".c-tabs-item__content h3 a"):
                mangas.append({
                    "name": a.text.strip(),
                    "url": a["href"]
                })

            return mangas

        except Exception as e:
            print("Erro busca:", e)
            return []

    # ==============================
    # 📖 CAPÍTULOS
    # ==============================
    async def get_chapters(self, manga):
        try:
            r = self.scraper.get(manga["url"], timeout=20)
            soup = BeautifulSoup(r.text, "lxml")

            chapters = []
            for a in soup.select("li.wp-manga-chapter a"):
                chapters.append({
                    "name": a.text.strip(),
                    "url": a["href"],
                    "manga": manga
                })

            chapters.reverse()
            return chapters

        except Exception as e:
            print("Erro capítulos:", e)
            return []

    # ==============================
    # 📥 DOWNLOAD + CBZ
    # ==============================
    async def download_chapter(self, chapter):
        r = self.scraper.get(chapter["url"], timeout=30)
        soup = BeautifulSoup(r.text, "lxml")

        imgs = []
        for img in soup.select(".reading-content img"):
            if img.get("data-src"):
                imgs.append(img["data-src"])
            elif img.get("src"):
                imgs.append(img["src"])

        if not imgs:
            raise Exception("Sem imagens")

        folder = Path("cache") / chapter["name"].replace(" ", "_")
        folder.mkdir(parents=True, exist_ok=True)

        paths = []

        for i, img_url in enumerate(imgs):
            try:
                ext = img_url.split(".")[-1].split("?")[0]
                path = folder / f"{i+1}.{ext}"

                img_data = self.scraper.get(img_url, timeout=30).content

                with open(path, "wb") as f:
                    f.write(img_data)

                paths.append(path)

            except Exception:
                continue

        cbz_path = folder.with_suffix(".cbz")

        with ZipFile(cbz_path, "w") as zipf:
            for img_path in paths:
                zipf.write(img_path, img_path.name)

        # Limpeza Railway
        for img_path in paths:
            os.remove(img_path)

        folder.rmdir()

        return cbz_path
