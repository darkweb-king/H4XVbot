import os
import json
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import nest_asyncio

# Telegram Token
TOKEN = "7921228482:AAEqy_qCaT4Ne79_hj5eX0JvEHKsRon9-KY"
ADMIN_ID = 7154259764  # your Telegram ID
CHANNELS = ["@hackwithdroid", "@CodesHubTools"]
USER_FILE = "users.json"

# Flask app for Render
app = Flask(__name__)
nest_asyncio.apply()

# Load users
def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USER_FILE, "w") as f:
            json.dump(users, f)

# Force Join Checker
async def is_joined(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    if not await is_joined(user_id, context):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/hackwithdroid")],
            [InlineKeyboardButton("🛠 Join Channel 2", url="https://t.me/CodesHubTools")],
            [InlineKeyboardButton("👤 Contact Admin", url="https://t.me/meowx00")]
        ]
        await update.message.reply_text("🚫 You must join both channels to use the bot:", reply_markup=InlineKeyboardMarkup(buttons))
        return
    msg = (
        "👋 Welcome to FreeFire Like Bot!\n\n"
        "✅ Use this command to send likes:\n"
        "`/like 12345678`\n\n"
        "📦 Multiple IDs:\n"
        "`/like 1234 5678 9999`\n\n"
        "📊 Use `/stats` to check users.\n"
        "📣 Use `/sendpost` to broadcast (admin only)."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# Like Command
async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)
    if not await is_joined(user_id, context):
        await start(update, context)
        return
    if not context.args:
        await update.message.reply_text("⚠️ Please provide FreeFire UID(s).\nUse: `/like 12345678`", parse_mode="Markdown")
        return
    results = []
    for uid in context.args:
        results.append(f"✅ Like sent to UID `{uid}`")
    await update.message.reply_text("\n".join(results), parse_mode="Markdown")

# SendPost (Admin only)
async def sendpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized to use this.")
        return
    await update.message.reply_text("📨 Send the post content (text/image/video)...")
    context.user_data["awaiting_post"] = True

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_post"):
        users = load_users()
        for uid in users:
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=uid, text=update.message.text)
                elif update.message.photo:
                    await context.bot.send_photo(chat_id=uid, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                elif update.message.video:
                    await context.bot.send_video(chat_id=uid, video=update.message.video.file_id, caption=update.message.caption)
            except:
                continue
        await update.message.reply_text("✅ Post sent to all users.")
        context.user_data["awaiting_post"] = False

# Stats (Admin only)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized.")
        return
    users = load_users()
    await update.message.reply_text(f"📊 Total users: {len(users)}")

# Run Bot
def run_bot():
    asyncio.run(start_bot())

async def start_bot():
    app_ = ApplicationBuilder().token(TOKEN).build()
    app_.add_handler(CommandHandler("start", start))
    app_.add_handler(CommandHandler("like", like))
    app_.add_handler(CommandHandler("sendpost", sendpost))
    app_.add_handler(CommandHandler("stats", stats))
    app_.add_handler(MessageHandler(None, handle_reply))
    print("🤖 Bot is running...")
    await app_.run_polling()

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
