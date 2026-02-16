import asyncio
from pathlib import Path
from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import env_vars
from tools.aqueue import AQueue
from fontes.mangalivre import MangaLivreClient

# -----------------------------
bot = Client(
    "bot",
    api_id=int(env_vars.get("API_ID")),
    api_hash=env_vars.get("API_HASH"),
    bot_token=env_vars.get("BOT_TOKEN")
)

# -----------------------------
pdf_queue = AQueue()
mangas = {}       # Resultados de busca
chapters = {}     # Capítulos
locks = {}        # Locks por usuário
mangalivre = MangaLivreClient()

# -----------------------------
async def get_user_lock(user_id):
    if user_id not in locks:
        locks[user_id] = asyncio.Lock()
    return locks[user_id]

# -----------------------------
# Comando /buscar
@bot.on_message(filters.command(["buscar"]))
async def buscar(client, message):
    if len(message.command) < 2:
        await message.reply("Use: /buscar <nome do mangá/manhwa>")
        return

    query = " ".join(message.command[1:])
    results = await mangalivre.search(query)
    if not results:
        await message.reply("Nenhum resultado encontrado.")
        return

    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"manga_{i}")] for i, m in enumerate(results)]
    for i, m in enumerate(results):
        mangas[f"manga_{i}"] = m

    await message.reply("Resultados:", reply_markup=InlineKeyboardMarkup(buttons))

# -----------------------------
# Seleção de manga
@bot.on_callback_query(filters.regex(r"^manga_"))
async def select_manga(client, callback):
    manga = mangas[callback.data]
    chap_list = await mangalivre.get_chapters(manga)
    if not chap_list:
        await callback.message.edit("Nenhum capítulo encontrado.")
        return

    for i, ch in enumerate(chap_list):
        chapters[f"chapter_{i}"] = ch

    buttons = [[InlineKeyboardButton(ch["name"], callback_data=f"chapter_{i}")] for i, ch in enumerate(chap_list)]
    await callback.message.edit(f"Capítulos de {manga['name']}:", reply_markup=InlineKeyboardMarkup(buttons))

# -----------------------------
# Seleção de capítulo
@bot.on_callback_query(filters.regex(r"^chapter_"))
async def select_chapter(client, callback):
    chapter = chapters[callback.data]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Baixar este capítulo", callback_data=f"download_{callback.data}")],
        [InlineKeyboardButton("Baixar todos a partir deste", callback_data=f"download_from_{callback.data}")]
    ])
    await callback.message.edit(f"Selecionado: {chapter['name']}", reply_markup=keyboard)

# -----------------------------
# Função de download com apagamento imediato
async def process_download(chapters_list, user_id, client):
    lock = await get_user_lock(user_id)
    async with lock:
        for ch in chapters_list:
            try:
                cbz_path = await mangalivre.download_chapter(ch)
                await client.send_document(user_id, str(cbz_path))
                if cbz_path.exists():
                    cbz_path.unlink()
            except Exception as e:
                logger.exception(f"Erro ao baixar/enviar capítulo {ch['name']}: {e}")

# -----------------------------
# Callbacks de download
@bot.on_callback_query(filters.regex(r"^download_"))
async def download_chapter(client, callback):
    user_id = callback.from_user.id
    data = callback.data.split("_", 1)[1]

    if data.startswith("from_"):
        chapter = chapters[data.replace("from_", "")]
        manga_chapters = [c for c in chapters.values() if c["manga"] == chapter["manga"]]
        manga_chapters.sort(key=lambda x: x["name"])
        chapters_list = manga_chapters[manga_chapters.index(chapter):]
        await callback.message.edit(f"Iniciando download de {len(chapters_list)} capítulo(s)...")
    else:
        chapter = chapters[data]
        chapters_list = [chapter]
        await callback.message.edit(f"Iniciando download de {chapter['name']}...")

    await process_download(chapters_list, user_id, client)
    await callback.message.edit("Download concluído e capítulos enviados!")

# -----------------------------
# Inicialização do cache
if __name__ == "__main__":
    Path("cache").mkdir(exist_ok=True)
    logger.info("Bot iniciado com sucesso!")
    bot.run()
