import os
import aiohttp
import zipfile
import asyncio
from io import BytesIO
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Client(
    "manga-bot-ptbr",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= UTIL =================

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as r:
            return await r.text()

# ================= FONTE 1 - MangaLivre =================

async def search_mangalivre(query):
    url = f"https://mangalivre.net/pesquisa?q={query.replace(' ', '+')}"
    html = await fetch(url)
    soup = BeautifulSoup(html, "lxml")

    results = []
    for item in soup.select(".seriesList li")[:5]:
        title = item.select_one("h3").text.strip()
        link = item.select_one("a")["href"]
        results.append({"title": title, "url": link})

    return results

async def get_chapters_mangalivre(manga_url):
    html = await fetch(manga_url)
    soup = BeautifulSoup(html, "lxml")

    chapters = []
    for cap in soup.select(".chapter-list li")[:20]:
        link = cap.select_one("a")["href"]
        name = cap.text.strip()
        chapters.append({"name": name, "url": link})

    return chapters

async def download_chapter_images(chapter_url):
    html = await fetch(chapter_url)
    soup = BeautifulSoup(html, "lxml")

    images = []
    for img in soup.select(".viewer img"):
        images.append(img["src"])

    return images

# ================= BOT =================

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🇧🇷 Envie o nome do mangá para buscar.")

@app.on_message(filters.text & filters.private)
async def search(client, message):

    query = message.text
    results = await search_mangalivre(query)

    if not results:
        await message.reply("❌ Nenhum resultado encontrado.")
        return

    buttons = [
        [InlineKeyboardButton(r["title"], callback_data=r["url"])]
        for r in results
    ]

    await message.reply(
        "Selecione o mangá:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query()
async def callbacks(client, callback):

    manga_url = callback.data

    chapters = await get_chapters_mangalivre(manga_url)

    if not chapters:
        await callback.message.edit("❌ Nenhum capítulo encontrado.")
        return

    buttons = [
        [InlineKeyboardButton(c["name"], callback_data=c["url"])]
        for c in chapters[:10]
    ]

    await callback.message.edit(
        "Selecione o capítulo:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    await callback.answer()

@app.on_callback_query()
async def download_handler(client, callback):

    chapter_url = callback.data

    if not chapter_url.startswith("http"):
        return

    await callback.message.edit("📥 Baixando capítulo...")

    images = await download_chapter_images(chapter_url)

    if not images:
        await callback.message.edit("❌ Erro ao baixar imagens.")
        return

    # Criar CBZ em memória
    cbz_buffer = BytesIO()
    with zipfile.ZipFile(cbz_buffer, "w") as z:
        async with aiohttp.ClientSession() as session:
            for i, img_url in enumerate(images):
                async with session.get(img_url) as r:
                    if r.status == 200:
                        z.writestr(f"{i}.jpg", await r.read())

    cbz_buffer.seek(0)

    await client.send_document(
        callback.message.chat.id,
        cbz_buffer,
        file_name="capitulo.cbz"
    )

    await callback.answer()

# ================= RUN =================

app.run()
