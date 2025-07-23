import configparser
import logging
import asyncio
from flask import Flask, request
import telegram

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper function for Telegram MarkdownV2 ---
def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2."""
    # List of characters to escape
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # Use a translation table for efficiency
    return str(text).translate(str.maketrans({char: '\\' + char for char in escape_chars}))

# --- Flask App and Configuration ---
app = Flask(__name__)

config = configparser.ConfigParser()

try:
    config.read('config.ini')
    telegram_token = config.get('TELEGRAM', 'TOKEN')
    chat_id_string = config.get('TELEGRAM', 'CHAT_ID', fallback='')

    if not telegram_token:
        logger.error("TELEGRAM 'TOKEN' not found in config.ini. Exiting.")
        exit()

except (configparser.NoSectionError, FileNotFoundError):
    logger.error("config.ini not found or [TELEGRAM] section is missing. Please create it.")
    exit()

# Split chat IDs, filter out any empty strings
chat_ids = [chat_id.strip() for chat_id in chat_id_string.split(',') if chat_id.strip()]

if not chat_ids:
    logger.warning("No chat IDs found in config.ini. The bot will receive webhooks but won't send notifications.")

bot = telegram.Bot(token=telegram_token)
logger.info(f"Bot initialized. Ready to send notifications to {len(chat_ids)} chat(s).")


# --- Asynchronous function to send a single message ---
async def send_telegram_message(chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
        logger.info(f"Successfully sent notification to chat_id: {chat_id}")
    except telegram.error.TelegramError as e:
        logger.error(f"Failed to send message to chat_id {chat_id}. Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending to {chat_id}. Error: {e}")


# --- Asynchronous function to gather all message tasks and run them ---
async def send_all_messages(chat_ids_list, message):
    tasks = [send_telegram_message(chat_id, message) for chat_id in chat_ids_list]
    await asyncio.gather(*tasks)


@app.route('/webhook', methods=['POST'])
def woocommerce_webhook():
    """Receives webhook from WooCommerce and sends a Telegram notification."""

    if not request.is_json:
        logger.warning("Received a non-JSON request. Rejecting with 400.")
        return "Request does not appear to be JSON", 400

    order_data = request.get_json()
    logger.info(f"Successfully parsed JSON. Order ID: {order_data.get('id', 'N/A')}")

    # --- Create a more detailed and safer message ---
    order_id = order_data.get('id', 'N/A')
    total_price = order_data.get('total', 'N/A')
    currency = order_data.get('currency', '')
    status = order_data.get('status', 'N/A')
    first_name = order_data.get('billing', {}).get('first_name', '')
    last_name = order_data.get('billing', {}).get('last_name', '')

    # --- NEW: Extract Line Items ---
    line_items = order_data.get('line_items', [])
    items_list_str = ""
    if line_items:
        for item in line_items:
            # Escape the item name as it's user-generated content that could break markdown
            item_name = escape_markdown_v2(item.get('name', 'N/A'))
            quantity = item.get('quantity', 0)
            items_list_str += f"• {quantity}x {item_name}\n"
    else:
        items_list_str = "No items found in webhook data\n"

    # --- Assemble the final message ---
    message = (
        f"🎉 *New Order Received*\n\n"
        f"*Order ID:* `{order_id}`\n"
        f"*Status:* {escape_markdown_v2(status)}\n"
        f"*Customer:* {escape_markdown_v2(first_name)} {escape_markdown_v2(last_name)}\n"
        f"*Total Price:* `{total_price} {currency}`\n\n"
        f"🛍️ *Items Purchased:*\n"
        f"{items_list_str}"
    )

    # --- Run all the message tasks at once ---
    if chat_ids:
        asyncio.run(send_all_messages(chat_ids, message))

    return "Webhook received successfully", 200

if __name__ == '__main__':
    # For production, you should use a proper WSGI server like Gunicorn or uWSGI
    app.run(host='0.0.0.0', port=443)