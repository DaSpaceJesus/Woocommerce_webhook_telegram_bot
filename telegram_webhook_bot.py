# Replace your old woocommerce_webhook function with this one.
# The rest of your script stays the same.

@app.route('/webhook', methods=['POST'])
def woocommerce_webhook():
    """Receives webhook from WooCommerce and sends a Telegram notification."""

    # --- NEW DEBUGGING LOGS ---
    # We will log everything we receive before we try to process it.
    logger.info("--- New Request Received ---")
    try:
        logger.info(f"Request Headers: {dict(request.headers)}")
        logger.info(f"Request Raw Body: {request.get_data(as_text=True)}")
        logger.info(f"Flask's 'is_json' check result: {request.is_json}")
    except Exception as e:
        logger.error(f"Error during initial logging: {e}")
    logger.info("--- End of Raw Request Data ---")
    # --- END OF DEBUGGING LOGS ---


    # Check if the request has JSON data
    if not request.is_json:
        logger.warning("Condition 'if not request.is_json' was TRUE. Rejecting with 400.")
        return "Request does not appear to be JSON", 400

    try:
        order_data = request.get_json()
        if not order_data:
            logger.warning("Request had JSON mime type, but body was empty or invalid.")
            return "JSON body is empty or invalid", 400
    except Exception as e:
        logger.error(f"Failed to parse JSON body. Error: {e}")
        return "Failed to parse JSON body", 400


    logger.info(f"Successfully parsed JSON. Order ID: {order_data.get('id', 'N/A')}")

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
