from pyrogram import Client
from app.config import API_ID, API_HASH, BOT_TOKEN
from app.services.queue_service import ChapterQueue
from app.services.chapter_service import process_chapter

app = Client(
    "manga-bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

queue = ChapterQueue()


@app.on_message()
async def handler(client, message):
    # exemplo simples
    chapter = "mock_chapter"
    await queue.add(message.chat.id, chapter)


@app.on_start()
async def start_worker():
    await queue.start_worker(
        lambda chat_id, chapter: process_chapter(app, chat_id, chapter)
)
