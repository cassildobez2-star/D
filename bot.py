import asyncio
import os
from pathlib import Path
from loguru import logger
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from config import env_vars
from fontes.mangalivre import MangaLivreClient

from sources.mangadex import MangaDexClient

source = MangaDexClient()

# =====================================
# 🔐 Verificação de variáveis obrigatórias
# =====================================
if not env_vars.get("API_ID") or not env_vars.get("API_HASH") or not env_vars.get("BOT_TOKEN"):
    raise ValueError("Variáveis API_ID, API_HASH ou BOT_TOKEN não configuradas.")

# =====================================
# 🚀 Inicialização do bot
# =====================================
bot = Client(
    "bot",
    api_id=int(env_vars.get("API_ID")),
    api_hash=env_vars.get("API_HASH"),
    bot_token=env_vars.get("BOT_TOKEN"),
    workers=10
)

mangalivre = MangaLivreClient()

mangas = {}
chapters = {}
locks = {}

# =====================================
# 🔒 Lock por usuário
# =====================================
async def get_user_lock(user_id):
    if user_id not in locks:
        locks[user_id] = asyncio.Lock()
    return locks[user_id]

# =====================================
# ✅ Comando /start
# =====================================
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("✅ Yuki308 online e funcionando!")

# =====================================
# 🔎 Comando /buscar
# =====================================
@bot.on_message(filters.command("buscar"))
async def buscar(client, message):
    try:
        if len(message.command) < 2:
            await message.reply("Use: /buscar <nome do mangá>")
            return

        query = " ".join(message.command[1:])
        await message.reply("🔎 Buscando...")

        results = await mangalivre.search(query)

        if not results:
            await message.reply("❌ Nenhum resultado encontrado.")
            return

        buttons = []
        for i, m in enumerate(results[:15]):  # Limita para evitar flood
            key = f"manga_{message.id}_{i}"
            mangas[key] = m
            buttons.append([InlineKeyboardButton(m["name"], callback_data=key)])

        await message.reply("📚 Resultados:", reply_markup=InlineKeyboardMarkup(buttons))

    except Exception as e:
        logger.exception(e)
        await message.reply("❌ Erro ao buscar.")

# =====================================
# 📖 Seleção de mangá
# =====================================
@bot.on_callback_query(filters.regex(r"^manga_"))
async def select_manga(client, callback):
    try:
        if callback.data not in mangas:
            await callback.answer("Expirado.", show_alert=True)
            return

        manga = mangas[callback.data]
        chap_list = await mangalivre.get_chapters(manga)

        if not chap_list:
            await callback.message.edit("❌ Nenhum capítulo encontrado.")
            return

        buttons = []
        for i, ch in enumerate(chap_list[:30]):  # Limite segurança
            key = f"chapter_{callback.message.id}_{i}"
            chapters[key] = ch
            buttons.append([InlineKeyboardButton(ch["name"], callback_data=key)])

        await callback.message.edit(
            f"📖 Capítulos de {manga['name']}:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logger.exception(e)
        await callback.message.edit("❌ Erro ao carregar capítulos.")

# =====================================
# 📥 Seleção de capítulo
# =====================================
@bot.on_callback_query(filters.regex(r"^chapter_"))
async def select_chapter(client, callback):
    try:
        if callback.data not in chapters:
            await callback.answer("Expirado.", show_alert=True)
            return

        chapter = chapters[callback.data]

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Baixar este capítulo", callback_data=f"download_{callback.data}")]
        ])

        await callback.message.edit(
            f"Selecionado:\n{chapter['name']}",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.exception(e)

# =====================================
# 📦 Download seguro com limpeza imediata
# =====================================
@bot.on_callback_query(filters.regex(r"^download_"))
async def download_chapter(client, callback):
    try:
        key = callback.data.replace("download_", "")

        if key not in chapters:
            await callback.answer("Expirado.", show_alert=True)
            return

        chapter = chapters[key]
        user_id = callback.from_user.id

        await callback.message.edit("⬇️ Baixando...")

        lock = await get_user_lock(user_id)

        async with lock:
            cbz_path = await mangalivre.download_chapter(chapter)

            try:
                await client.send_document(user_id, str(cbz_path))
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_document(user_id, str(cbz_path))

            # 🔥 Apaga imediatamente após envio
            if cbz_path.exists():
                cbz_path.unlink()

        await callback.message.edit("✅ Capítulo enviado!")

    except Exception as e:
        logger.exception(e)
        await callback.message.edit("❌ Erro no download.")

# =====================================
# 🚀 Inicialização
# =====================================
if __name__ == "__main__":
    Path("cache").mkdir(exist_ok=True)

    logger.info("🚀 Bot iniciado no Railway!")
    bot.run()
