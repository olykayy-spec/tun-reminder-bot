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
    """Start scheduler AFTER the event loop is ready"""
    if not scheduler.running:
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
    
    try:
        task_id = int(context.args[0])
        mark_done(task_id)
        await update.message.reply_text("✅ Task marked as done!")
    except ValueError:
        await update.message.reply_text("❗ Please provide a valid task ID")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ================= REMINDERS =================
async def send_reminder(application: Application, user_id: int):
    """Send reminder to user"""
    tasks = get_tasks(user_id)
    if tasks:
        msg = "⏰ Reminder:\n"
        for t in tasks:
            msg += f"- {t[1]}\n"
        await application.bot.send_message(chat_id=user_id, text=msg)

async def start_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Remove existing job if any
    try:
        scheduler.remove_job(str(user_id))
    except:
        pass
    
    # Add new reminder job - FIXED: pass application and user_id correctly
    scheduler.add_job(
        send_reminder,
        trigger="interval",
        minutes=30,
        args=[context.application, user_id],  # Fixed: pass application and user_id
        id=str(user_id),
        replace_existing=True,
    )
    
    await update.message.reply_text("⏱ Reminders started (every 30 minutes)")

# ================= MAIN =================
def main():
    """Main function to run the bot"""
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable not set!")
        return
    
    # Build application
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("start_reminders", start_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot is running...")
    
    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
