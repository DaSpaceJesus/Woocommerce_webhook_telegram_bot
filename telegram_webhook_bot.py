import configparser
from flask import Flask, request, abort
import telegram

app = Flask(__name__)
config = configparser.ConfigParser()
config.read('config.ini')

telegram_token = config['TELEGRAM']['TOKEN']
telegram_chat_id = config['TELEGRAM']['CHAT_ID']

bot = telegram.Bot(token=telegram_token)

@app.route('/webhook', methods=['POST'])
def woocommerce_webhook():
    order_data = request.get_json()

    message = f"New Order Received\nOrder ID: {order_data['id']}\nTotal Price: {order_data['total']}"

    bot.send_message(chat_id=telegram_chat_id, text=message)
    return "Webhook received", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 4430)