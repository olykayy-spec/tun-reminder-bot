import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import add_task, get_tasks, mark_done

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ================= SCHEDULER =================
scheduler = AsyncIOScheduler()

async def post_init(application: Application):
    # Start scheduler AFTER the event loop is ready
    scheduler.start()

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Daily Reminder Bot\n\n"
        "/add - Add a task\n"
        "/list - View tasks\n"
        "/done <id> - Mark task as done\n"
        "/start_reminders - Start reminders"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adding"] = True
    await update.message.reply_text("✍️ Send me the task")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("adding"):
        add_task(update.message.from_user.id, update.message.text)
        context.user_data["adding"] = False
        await update.message.reply_text("✅ Task added!")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = get_tasks(update.message.from_user.id)
    if not tasks:
        await update.message.reply_text("🎉 No pending tasks")
        return

    msg = "📋 Your tasks:\n"
    for t in tasks:
        msg += f"{t[0]}. {t[1]}\n"
    msg += "\nUse /done <id> when finished"
    await update.message.reply_text(msg)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Use /done <task_id>")
        return

    task_id = int(context.args[0])
    mark_done(task_id)
    await update.message.reply_text("✅ Task marked as done!")

# ================= REMINDERS =================
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data
    tasks = get_tasks(user_id)

    if tasks:
        msg = "⏰ Reminder:\n"
        for t in tasks:
            msg += f"- {t[1]}\n"
        await context.bot.send_message(chat_id=user_id, text=msg)

async def start_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # One reminder job per user
    scheduler.add_job(
        send_reminder,
        trigger="interval",
        minutes=30,
        args=[context],
        id=str(user_id),
        replace_existing=True,
        data=user_id,
    )

    await update.message.reply_text("⏱ Reminders started (every 30 minutes)")

# ================= APP =================
app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(post_init)
    .build()
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_tasks))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("start_reminders", start_reminders))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
