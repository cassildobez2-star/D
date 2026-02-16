import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from zipfile import ZipFile


class MangaLivreClient:
    name = "MangaLivre"
    base_url = "https://mangalivre.tv"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": base_url
    }

    # ==========================================
    # 🔎 BUSCA CORRIGIDA (funciona em Madara)
    # ==========================================
    async def search(self, query: str):
        try:
            url = f"{self.base_url}/?s={query}&post_type=wp-manga"
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(r.text, "lxml")

            mangas = []
            for a in soup.select(".c-tabs-item__content h3 a"):
                mangas.append({
                    "name": a.text.strip(),
                    "url": a["href"]
                })

            return mangas

        except Exception:
            return []

    # ==========================================
    # 📖 CAPÍTULOS
    # ==========================================
    async def get_chapters(self, manga):
        try:
            r = requests.get(manga["url"], headers=self.headers, timeout=15)
            soup = BeautifulSoup(r.text, "lxml")

            chapters = []
            for a in soup.select("li.wp-manga-chapter a"):
                chapters.append({
                    "name": a.text.strip(),
                    "url": a["href"],
                    "manga": manga
                })

            chapters.reverse()  # Ordem correta

            return chapters

        except Exception:
            return []

    # ==========================================
    # 📥 DOWNLOAD + CBZ
    # ==========================================
    async def download_chapter(self, chapter):
        r = requests.get(chapter["url"], headers=self.headers, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")

        imgs = []
        for img in soup.select(".reading-content img"):
            if img.get("data-src"):
                imgs.append(img["data-src"])
            elif img.get("src"):
                imgs.append(img["src"])

        if not imgs:
            raise Exception("Sem imagens no capítulo")

        folder = Path("cache") / chapter["name"].replace(" ", "_")
        folder.mkdir(parents=True, exist_ok=True)

        paths = []

        for i, img_url in enumerate(imgs):
            try:
                ext = img_url.split(".")[-1].split("?")[0]
                path = folder / f"{i+1}.{ext}"

                img_data = requests.get(img_url, headers=self.headers, timeout=20).content
                with open(path, "wb") as f:
                    f.write(img_data)

                paths.append(path)

            except Exception:
                continue

        cbz_path = folder.with_suffix(".cbz")

        with ZipFile(cbz_path, "w") as zipf:
            for img_path in paths:
                zipf.write(img_path, img_path.name)

        # Limpeza imediata para Railway
        for img_path in paths:
            os.remove(img_path)

        folder.rmdir()

        return cbz_path
