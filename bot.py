import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
import nest_asyncio
import asyncio

TOKEN = "7921228482:AAEqy_qCaT4Ne79_hj5eX0JvEHKsRon9-KY"

app = Flask(__name__)
nest_asyncio.apply()

# Bot logic
async def start(update, context):
    await update.message.reply_text("🤖 Welcome to the bot!")

application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

def run_bot():
    print("🤖 Bot is running...")
    asyncio.run(application.run_polling())

@app.route('/')
def home():
    return "Bot is running on Render!"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
