import configparser
import sys
import time
from datetime import datetime, timedelta

from telegram.ext import Updater, CommandHandler, CallbackContext
from woocommerce import API

# --- Configuration ---
# The bot will check for new orders at this interval (in seconds)
CHECK_INTERVAL_SECONDS = 300  # 300 seconds = 5 minutes

# --- Global variable to store the ID of the last processed order ---
# This prevents sending duplicate notifications when the bot restarts.
LATEST_PROCESSED_ORDER_ID = 0


def load_config():
    """Loads credentials from the config.ini file."""
    config = configparser.ConfigParser()
    try:
        config.read_file(open('config.ini'))
        return {
            'wc_url': config['woocommerce']['url'],
            'wc_key': config['woocommerce']['key'],
            'wc_secret': config['woocommerce']['secret'],
            'tg_token': config['telegram']['token'],
            'tg_chat_id': config['telegram']['chat_id']
        }
    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR: config.ini file not found or is incomplete. Missing key: {e}")
        sys.exit(1)


def format_order_message(order):
    """Formats the order data into a user-friendly message."""
    message = f"🎉 *New Order Received!* 🎉\n\n"
    message += f"*Order ID:* #{order['id']}\n"
    message += f"*Customer:* {order['billing']['first_name']} {order['billing']['last_name']}\n"
    message += f"*Total Amount:* {order['total']} {order['currency']}\n\n"
    message += "*Items:*\n"
    for item in order['line_items']:
        message += f"  - {item['name']} (x{item['quantity']})\n"

    # Use MarkdownV2 for formatting. Note that some characters need to be escaped.
    # For simplicity, we are not escaping all possible characters here.
    return message.replace('.', '\\.')


def start_command(update, context):
    """Handler for the /start command."""
    user = update.effective_user
    update.message.reply_text(
        f"Hi {user.first_name}! I am your WooCommerce Order Bot.\n"
        f"I will notify you here about new orders.\n"
        f"Use /testapi to check the connection to your store."
    )


def test_api_command(update, context):
    """Handler for the /testapi command. Checks the WooCommerce connection."""
    update.message.reply_text("Connecting to WooCommerce API to test connection...")
    try:
        wcapi = context.bot_data['wcapi']
        # The 'system_status' endpoint is a lightweight way to check for a valid connection.
        response = wcapi.get("system_status")
        if response.status_code == 200:
            store_version = response.json().get('environment', {}).get('version', 'N/A')
            update.message.reply_text(f"✅ Connection successful!\nWooCommerce Version: {store_version}")
        else:
            update.message.reply_text(f"❌ Connection failed. Status Code: {response.status_code}")
    except Exception as e:
        update.message.reply_text(f"❌ An error occurred during connection: {e}")


def check_for_new_orders(context: CallbackContext):
    """
    This function is called by the job queue to poll for new orders.
    """
    global LATEST_PROCESSED_ORDER_ID

    wcapi = context.bot_data['wcapi']
    chat_id = context.bot_data['chat_id']

    print(f"[{datetime.now()}] Checking for new orders since ID: {LATEST_PROCESSED_ORDER_ID}...")

    try:
        # Fetch orders created in the last 24 hours to be safe.
        # WooCommerce API uses ISO 8601 format for dates.
        after_date = (datetime.now() - timedelta(days=1)).isoformat()

        orders = wcapi.get("orders", params={'after': after_date, 'orderby': 'id', 'order': 'asc'}).json()

        new_orders_found = []
        for order in orders:
            if order['id'] > LATEST_PROCESSED_ORDER_ID:
                new_orders_found.append(order)

        if new_orders_found:
            print(f"Found {len(new_orders_found)} new order(s).")
            for order in new_orders_found:
                message = format_order_message(order)
                context.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2')
                # Update the latest ID to the one we just processed
                LATEST_PROCESSED_ORDER_ID = order['id']
                time.sleep(1)  # Small delay between sending multiple notifications
        else:
            print("No new orders found.")

    except Exception as e:
        print(f"An error occurred while checking for orders: {e}")


def main():
    """Starts the Telegram bot and the background job."""
    global LATEST_PROCESSED_ORDER_ID

    # --- Step 1: Load all credentials ---
    config = load_config()

    # --- Step 2: Initialize WooCommerce API ---
    try:
        wcapi = API(
            url=config['wc_url'],
            consumer_key=config['wc_key'],
            consumer_secret=config['wc_secret'],
            version="wc/v3",
            timeout=20
        )
        # Fetch the very last order to initialize our counter
        latest_orders = wcapi.get("orders", params={'per_page': 1}).json()
        if latest_orders:
            LATEST_PROCESSED_ORDER_ID = latest_orders[0]['id']
        print(f"WooCommerce API connected. Last order ID is: {LATEST_PROCESSED_ORDER_ID}")
    except Exception as e:
        print(f"FATAL: Could not connect to WooCommerce API on startup. Error: {e}")
        sys.exit(1)

    # --- Step 3: Set up the Telegram Bot ---
    updater = Updater(config['tg_token'], use_context=True)
    dispatcher = updater.dispatcher

    # Store the wcapi and chat_id objects in the bot_data context so handlers can access them
    dispatcher.bot_data['wcapi'] = wcapi
    dispatcher.bot_data['chat_id'] = config['tg_chat_id']

    # --- Step 4: Register command handlers ---
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("testapi", test_api_command))

    # --- Step 5: Set up and start the recurring job ---
    job_queue = updater.job_queue
    job_queue.run_repeating(check_for_new_orders, interval=CHECK_INTERVAL_SECONDS, first=10)

    # --- Step 6: Start the bot ---
    updater.start_polling()
    print("Telegram bot started. Polling for commands and checking for orders...")
    updater.idle()


if __name__ == '__main__':
    main()
