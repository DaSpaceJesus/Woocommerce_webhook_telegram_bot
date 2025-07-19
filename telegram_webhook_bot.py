import configparser
import logging
from flask import Flask, request, abort
import telegram

# --- Basic Logging Setup ---
# This will help you see what's happening and debug issues.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flask App and Configuration ---
app = Flask(__name__)
config = configparser.ConfigParser()

try:
    config.read('config.ini')
    # Use .get() for safer access to config values
    telegram_token = config.get('TELEGRAM', 'TOKEN')
    chat_id_string = config.get('TELEGRAM', 'CHAT_ID', fallback='')  # Fallback to empty string if not found

    if not telegram_token:
        logger.error("TELEGRAM 'TOKEN' not found in config.ini. Exiting.")
        exit()

except (configparser.NoSectionError, FileNotFoundError):
    logger.error("config.ini not found or [TELEGRAM] section is missing. Please create it.")
    exit()

# Split chat IDs, filter out any empty strings that might result from extra commas
chat_ids = [chat_id.strip() for chat_id in chat_id_string.split(',') if chat_id.strip()]

if not chat_ids:
    logger.warning("No chat IDs found in config.ini. The bot will receive webhooks but won't send notifications.")

bot = telegram.Bot(token=telegram_token)
logger.info(f"Bot initialized. Ready to send notifications to {len(chat_ids)} chat(s).")


@app.route('/webhook', methods=['POST'])
def woocommerce_webhook():
    """Receives webhook from WooCommerce and sends a Telegram notification."""

    # Check if the request has JSON data
    if not request.is_json:
        logger.warning("Received a non-JSON request to webhook endpoint.")
        return "Request must be JSON", 400

    order_data = request.get_json()
    logger.info(f"Received webhook for Order ID: {order_data.get('id', 'N/A')}")

    # --- Create a more detailed and safer message ---
    # Using .get() is safer than direct access like order_data['key']
    order_id = order_data.get('id', 'N/A')
    total_price = order_data.get('total', 'N/A')
    currency = order_data.get('currency', '')
    status = order_data.get('status', 'N/A')
    first_name = order_data.get('billing', {}).get('first_name', '')
    last_name = order_data.get('billing', {}).get('last_name', '')

    message = (
        f"🎉 *New Order Received* 🎉\n\n"
        f"*Order ID:* `{order_id}`\n"
        f"*Status:* `{status}`\n"
        f"*Customer:* {first_name} {last_name}\n"
        f"*Total Price:* `{total_price} {currency}`"
    )

    # --- Loop through chat IDs and send message ---
    for chat_id in chat_ids:
        try:
            bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
            logger.info(f"Successfully sent notification to chat_id: {chat_id}")
        except telegram.error.TelegramError as e:
            # This catches errors like "Chat not found" or "bot was blocked by the user"
            logger.error(f"Failed to send message to chat_id {chat_id}. Error: {e}")
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred while sending to {chat_id}. Error: {e}")

    return "Webhook received successfully", 200


if __name__ == '__main__':
    # For production, you should use a proper WSGI server like Gunicorn or uWSGI
    # Example: gunicorn --bind 0.0.0.0:4430 your_script_name:app
