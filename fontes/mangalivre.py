import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from zipfile import ZipFile

class MangaLivreClient:
    name = "MangaLivre"
    base_url = "https://mangalivre.tv"

    async def search(self, query: str):
        url = f"{self.base_url}/search?keyword={query}"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "lxml")
        mangas = []
        for a in soup.select("h3.manga-title a"):
            mangas.append({
                "name": a.text.strip(),
                "url": self.base_url + a["href"]
            })
        return mangas

    async def get_chapters(self, manga):
        r = requests.get(manga["url"])
        soup = BeautifulSoup(r.text, "lxml")
        chapters = []
        for li in soup.select("ul#chapter-list li a"):
            chapters.append({
                "name": li.text.strip(),
                "url": self.base_url + li["href"],
                "manga": manga
            })
        return chapters

    async def download_chapter(self, chapter):
        r = requests.get(chapter["url"])
        soup = BeautifulSoup(r.text, "lxml")
        imgs = [img["src"] for img in soup.select(".reading-content img")]
        folder = Path("cache") / chapter["name"].replace(" ", "_")
        folder.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, img_url in enumerate(imgs):
            ext = img_url.split(".")[-1].split("?")[0]
            path = folder / f"{i+1}.{ext}"
            with open(path, "wb") as f:
                f.write(requests.get(img_url).content)
            paths.append(path)

        # Criar CBZ
        cbz_name = folder.with_suffix(".cbz")
        with ZipFile(cbz_name, "w") as zipf:
            for img_path in paths:
                zipf.write(img_path, img_path.name)

        # Limpar pasta de imagens
        for img_path in paths:
            os.remove(img_path)
        folder.rmdir()

        return cbz_name
