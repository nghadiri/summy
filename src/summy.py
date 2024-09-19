import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from transformers import pipeline
import logging
from collections import defaultdict
from datetime import datetime

# Initialize summarization pipeline
summarizer = pipeline("summarization")

# Enable logging for the bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to load settings from appsettings.json
def load_settings():
    with open('appsettings.json', 'r') as file:
        return json.load(file)

# Function to summarize messages between two dates
def summarize_messages_by_user_in_date_range(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    
    # Extract the date range from the command arguments
    args = context.args
    if len(args) < 2:
        update.message.reply_text("Please provide a start and end datetime in the format: YYYY-MM-DD HH:MM")
        return

    try:
        start_date = datetime.strptime(args[0], "%Y-%m-%d %H:%M")
        end_date = datetime.strptime(args[1], "%Y-%m-%d %H:%M")
    except ValueError:
        update.message.reply_text("Invalid date format! Use: YYYY-MM-DD HH:MM")
        return

    # Retrieve the last 200 messages from the chat
    messages = context.bot.get_chat_history(chat_id, limit=200)

    # Dictionary to store messages grouped by user
    user_messages = defaultdict(list)

    # Group messages by user and filter by the provided date range
    for message in messages:
        if message.text and start_date <= message.date <= end_date:
            user_name = message.from_user.username or message.from_user.full_name
            user_messages[user_name].append(message.text)

    # Summarize each user's messages
    summary_by_user = []
    for user, msgs in user_messages.items():
        all_text = " ".join(msgs)

        if len(all_text) > 0:
            summary = summarizer(all_text, max_length=100, min_length=30, do_sample=False)
            summary_by_user.append(f"{user}: {summary[0]['summary_text']}")

    # Send the summarized text to the Telegram group
    if summary_by_user:
        final_summary = "\n\n".join(summary_by_user)
        update.message.reply_text(f"Summary by user from {start_date} to {end_date}:\n\n{final_summary}")
    else:
        update.message.reply_text(f"No messages found between {start_date} and {end_date}.")

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! Use /summarize_by_user_range to summarize messages in a date range. Format: /summarize_by_user_range YYYY-MM-DD HH:MM YYYY-MM-DD HH:MM')

def main():
    """Start the bot."""
    # Load settings from appsettings.json
    settings = load_settings()
    TOKEN = settings['TelegramBot']['Token']

    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Command to start the bot
    dispatcher.add_handler(CommandHandler("start", start))

    # Command to summarize messages by user within a date range
    dispatcher.add_handler(CommandHandler("summarize_by_user_range", summarize_messages_by_user_in_date_range))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM, or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
