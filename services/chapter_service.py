import tempfile
import shutil
from app.services.pdf_service import create_pdf

async def process_chapter(bot, chat_id, chapter):

    await bot.send_message(chat_id, "📥 Baixando capítulo...")

    with tempfile.TemporaryDirectory() as tmpdir:
        images = await chapter.download(tmpdir)

        pdf_path = await create_pdf(images, tmpdir)

        await bot.send_document(chat_id, pdf_path)

    # Diretório é apagado automaticamente
