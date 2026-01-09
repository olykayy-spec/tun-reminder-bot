import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import add_task, get_tasks, mark_done

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Daily Reminder Bot\n\n"
        "/add - Add task\n"
        "/list - View tasks\n"
        "/done <id> - Mark done\n"
        "/start_reminders - Start reminders"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

scheduler = AsyncIOScheduler()
scheduler.start()

print("Bot is running...")
app.run_polling()
