from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN
from services.manga_source import buscar_manga

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Bot de Mangá Online!\n\nUse:\n/buscar nome_do_manga"
    )

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Digite o nome do mangá.\nEx: /buscar naruto")
        return

    nome = " ".join(context.args)
    await update.message.reply_text("🔎 Buscando...")

    resultados = buscar_manga(nome)

    if not resultados:
        await update.message.reply_text("❌ Nada encontrado.")
        return

    resposta = "📖 Resultados:\n\n"
    for titulo, link in resultados:
        resposta += f"{titulo}\n{link}\n\n"

    await update.message.reply_text(resposta)

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN não configurado!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))

    print("Bot de mangá rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
