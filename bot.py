import os
import asyncio
import shutil
from pathlib import Path
from zipfile import ZipFile

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from loguru import logger

from sources.mangalivre import MangaLivreClient

# ========================
# CONFIG
# ========================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Configure as variáveis no Railway.")

bot = Client(
    "manga_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=2,
    max_concurrent_transmissions=2
)

source = MangaLivreClient()

# cache leve em memória
SEARCH_CACHE = {}
CHAPTER_CACHE = {}

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# ========================
# START
# ========================

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply(
        "📚 *Bot de Mangá PT-BR*\n\n"
        "Use:\n"
        "`/buscar nome_do_manga`",
        quote=True
    )

# ========================
# BUSCAR
# ========================

@bot.on_message(filters.command("buscar"))
async def buscar_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Use: /buscar nome_do_manga")

    query = " ".join(message.command[1:])

    msg = await message.reply("🔎 Buscando...")

    try:
        results = await source.search(query)
    except Exception as e:
        logger.error(e)
        return await msg.edit("❌ Erro na busca.")

    if not results:
        return await msg.edit("❌ Nenhum resultado encontrado.")

    SEARCH_CACHE[message.from_user.id] = results

    buttons = [
        [InlineKeyboardButton(m["name"], callback_data=f"manga_{i}")]
        for i, m in enumerate(results[:15])
    ]

    await msg.edit(
        "📖 Selecione:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ========================
# MANGÁ SELECIONADO
# ========================

@bot.on_callback_query(filters.regex(r"^manga_"))
async def manga_callback(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[1])

    if user_id not in SEARCH_CACHE:
        return await callback.answer("Sessão expirada.", show_alert=True)

    manga = SEARCH_CACHE[user_id][index]

    await callback.message.edit("📚 Carregando capítulos...")

    try:
        chapters = await source.get_chapters(manga)
    except Exception as e:
        logger.error(e)
        return await callback.message.edit("❌ Erro ao carregar capítulos.")

    if not chapters:
        return await callback.message.edit("❌ Nenhum capítulo encontrado.")

    CHAPTER_CACHE[user_id] = chapters

    buttons = [
        [InlineKeyboardButton(ch["name"], callback_data=f"chap_{i}")]
        for i, ch in enumerate(chapters[:50])
    ]

    await callback.message.edit(
        "📑 Escolha o capítulo:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ========================
# CAPÍTULO
# ========================

@bot.on_callback_query(filters.regex(r"^chap_"))
async def chapter_callback(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[1])

    if user_id not in CHAPTER_CACHE:
        return await callback.answer("Sessão expirada.", show_alert=True)

    chapter = CHAPTER_CACHE[user_id][index]

    msg = await callback.message.edit("📥 Baixando capítulo...")

    try:
        cbz_path = await source.download_chapter(chapter)
    except Exception as e:
        logger.error(e)
        return await msg.edit("❌ Erro ao baixar capítulo.")

    try:
        await callback.message.reply_document(
            document=str(cbz_path),
            caption=chapter["name"]
        )
    except Exception as e:
        logger.error(e)
        await msg.edit("❌ Erro ao enviar arquivo.")
    finally:
        # 🔥 LIMPEZA IMEDIATA PARA RAILWAY
        try:
            if os.path.exists(cbz_path):
                os.remove(cbz_path)
        except:
            pass

    await msg.delete()

# ========================
# IGNORAR OUTROS TEXTOS
# ========================

@bot.on_message()
async def ignore(client, message):
    pass

# ========================
# MAIN
# ========================

if __name__ == "__main__":
    logger.info("Bot iniciado.")
    bot.run()
