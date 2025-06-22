import logging
import requests
import nest_asyncio
import asyncio
import time
import os
import json
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ====== Bot Settings ======
TOKEN = "7921228482:AAEqy_qCaT4Ne79_hj5eX0JvEHKsRon9-KY"
ADMIN_ID = 7154259764
CHANNELS = ["@hackwithdroid", "@CodesHubTools"]
USERS_FILE = "user.json"
broadcast_msg = {}

# ====== Logging & Nest Asyncio ======
nest_asyncio.apply()
logging.basicConfig(level=logging.CRITICAL)

# ====== Flask App for Render ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running on Render!"

# ====== Save User ======
async def save_user(user_id):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
            except:
                users = []
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# ====== Force Join Check ======
async def check_joined(bot, user_id):
    for channel in CHANNELS:
        try:
            res = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if res.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# ====== Bot Commands ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_user(user.id)

    if not await check_joined(context.bot, user.id):
        keyboard = [
            [InlineKeyboardButton("🔗 Join @hackwithdroid", url="https://t.me/hackwithdroid")],
            [InlineKeyboardButton("🔗 Join @CodesHubTools", url="https://t.me/CodesHubTools")],
            [InlineKeyboardButton("👨‍💻 Admin Contact", url="https://t.me/meowx00")]
        ]
        await update.message.reply_text(
            "🚫 To use this bot, you must join both channels below:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "👋 *Welcome to SANATANI FF LIKE BOT!*\n\n"
        "🔥 Use this bot to send likes to Free Fire UIDs instantly.",
        parse_mode=ParseMode.MARKDOWN
    )
    await help_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🟢 *Commands:*\n\n"
        "`/like UID` - Send likes to one UID\n"
        "`/multi UID1 UID2 ...` - Multiple UIDs\n"
        "`/sendpost` - (admin) Broadcast post\n"
        "`/stats` - (admin) Bot user count",
        parse_mode=ParseMode.MARKDOWN
    )

async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(context.bot, update.effective_user.id):
        return await start(update, context)
    if len(context.args) != 1:
        return await update.message.reply_text("❌ Use: `/like UID`", parse_mode=ParseMode.MARKDOWN)
    await update.message.reply_text(get_like_data(context.args[0]), parse_mode=ParseMode.MARKDOWN)

async def multi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(context.bot, update.effective_user.id):
        return await start(update, context)
    if len(context.args) < 1:
        return await update.message.reply_text("❌ Use: `/multi UID1 UID2 ...`", parse_mode=ParseMode.MARKDOWN)
    messages = [get_like_data(uid) for uid in context.args]
    await update.message.reply_text("\n\n".join(messages), parse_mode=ParseMode.MARKDOWN)

def get_like_data(uid):
    try:
        r = requests.get(f"https://sanatani-ff-api.vercel.app/like?uid={uid}&server_name=ind", timeout=10)
        d = r.json()
        if d.get("status") != 1:
            return f"❌ UID `{uid}` – Invalid or not found."
        return (
            f"✅ *Likes sent to UID:* `{uid}`\n"
            f"🧑‍🎮 Nickname: `{d.get('PlayerNickname')}`\n"
            f"❤️ Before: `{d.get('LikesbeforeCommand')}`\n"
            f"💥 Given Now: `{d.get('LikesGivenByAPI')}`\n"
            f"🎉 After: `{d.get('LikesafterCommand')}`\n"
            f"🔧 By *Blackhat-Abhi*"
        )
    except:
        return f"⚠️ UID `{uid}` – API error."

async def sendpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("📢 Send your post (text/image/video)...")
    broadcast_msg[update.effective_user.id] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if broadcast_msg.get(update.effective_user.id):
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                try:
                    users = json.load(f)
                except:
                    users = []
        else:
            users = []

        count = 0
        for user in users:
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=int(user), text=update.message.text)
                elif update.message.photo:
                    await context.bot.send_photo(chat_id=int(user), photo=update.message.photo[-1].file_id, caption=update.message.caption)
                elif update.message.video:
                    await context.bot.send_video(chat_id=int(user), video=update.message.video.file_id, caption=update.message.caption)
                count += 1
            except:
                continue
        await update.message.reply_text(f"✅ Post sent to {count} users.")
        broadcast_msg.pop(update.effective_user.id, None)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            try:
                users = json.load(f)
                count = len(users)
            except:
                count = 0
    else:
        count = 0
    await update.message.reply_text(f"📊 Total users: {count}")

# ====== Telegram Bot Init ======
async def main():
    global app_bot
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("like", like))
    app_bot.add_handler(CommandHandler("multi", multi))
    app_bot.add_handler(CommandHandler("sendpost", sendpost))
    app_bot.add_handler(CommandHandler("stats", stats))
    app_bot.add_handler(MessageHandler(filters.ALL & filters.TEXT | filters.PHOTO | filters.VIDEO, handle_message))

    print("🤖 Bot is running...")
    await app_bot.run_polling()

# ====== Start Bot in Thread (for Flask) ======
def run_bot():
    asyncio.run(main())

# ====== Main Entry Point ======
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)