import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Bot de Mangá Online!")

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /buscar nome_do_manga")
        return

    nome = " ".join(context.args)
    await update.message.reply_text(f"🔎 Buscando por: {nome}")

def main():
    if not TOKEN:
        print("ERRO: BOT_TOKEN não encontrado!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))

    print("✅ Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
