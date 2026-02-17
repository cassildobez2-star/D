import os
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get("BOT_TOKEN")

def start(update, context):
    update.message.reply_text("🤖 Bot online!")

def main():
    if not TOKEN:
        print("BOT_TOKEN não encontrado!")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    print("Bot iniciado...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
