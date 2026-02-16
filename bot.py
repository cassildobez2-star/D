import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from loguru import logger
from sources.mangadex import MangaDexClient

# ==============================
# CONFIG
# ==============================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Variáveis de ambiente não configuradas.")

app = Client(
    "manga_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

source = MangaDexClient()

# Cache simples em memória
SEARCH_CACHE = {}
CHAPTER_CACHE = {}

# ==============================
# START
# ==============================

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply(
        "📚 Yuki308 Online\n\n"
        "Use:\n"
        "/buscar nome_do_manga"
    )

# ==============================
# BUSCAR
# ==============================

@app.on_message(filters.command("buscar"))
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

    buttons = []
    for i, manga in enumerate(results):
        buttons.append(
            [InlineKeyboardButton(manga["name"], callback_data=f"manga_{i}")]
        )

    await msg.edit(
        "📖 Selecione o mangá:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==============================
# ESCOLHER MANGÁ
# ==============================

@app.on_callback_query(filters.regex(r"^manga_"))
async def manga_selected(client, callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    if user_id not in SEARCH_CACHE:
        return await callback.answer("Sessão expirada.", show_alert=True)

    manga = SEARCH_CACHE[user_id][index]

    msg = await callback.message.edit("📚 Carregando capítulos...")

    try:
        chapters = await source.get_chapters(manga)
    except Exception as e:
        logger.error(e)
        return await msg.edit("❌ Erro ao buscar capítulos.")

    if not chapters:
        return await msg.edit("❌ Nenhum capítulo encontrado.")

    CHAPTER_CACHE[user_id] = chapters

    buttons = []
    for i, chapter in enumerate(chapters[:50]):  # Limite para evitar flood
        buttons.append(
            [InlineKeyboardButton(chapter["name"], callback_data=f"chap_{i}")]
        )

    await msg.edit(
        "📑 Selecione o capítulo:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==============================
# ESCOLHER CAPÍTULO
# ==============================

@app.on_callback_query(filters.regex(r"^chap_"))
async def chapter_selected(client, callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

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
        # 🔥 Limpeza Railway imediata
        try:
            if os.path.exists(cbz_path):
                os.remove(cbz_path)
        except:
            pass

    await msg.delete()

# ==============================
# ERROS GLOBAIS
# ==============================

@app.on_message()
async def ignore_other_messages(client, message):
    pass


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    logger.info("Bot iniciando...")
    app.run()
