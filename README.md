# WooCommerce to Telegram Order Notifier
A simple yet powerful Python bot that instantly sends new WooCommerce order notifications to one or more Telegram chats. This project uses a Flask web server to listen for WooCommerce webhooks and the python-telegram-bot library to dispatch alerts.


Features
Instant Notifications: Receive alerts in Telegram the moment a new order is placed.

Multi-Chat Support: Send notifications to multiple Telegram users or groups simultaneously.

Detailed Order Information: Messages include Order ID, status, customer name, total price, and a list of purchased items.

Easy Configuration: All settings (API tokens, chat IDs) are managed in a simple config.ini file.

Robust and Production-Ready: Includes instructions for deploying with Gunicorn and Nginx for a stable, production environment.

Secure: Keeps your sensitive API tokens and chat IDs separate from the main codebase.

No Domain Needed!


## How It Works
The data flow is straightforward:

WooCommerce: A customer places a new order.

Webhook Event: WooCommerce triggers the order.created event and sends a POST request with the order data to a predefined URL.

Flask Server: The Python Flask application, running on your server, listens on that URL. It receives and parses the incoming JSON data.

Telegram Bot: The script formats the order details into a clean message and uses the Telegram Bot API to send it to all the chat IDs specified in your configuration.

[WooCommerce Store] ---> [Webhook POST] ---> [Your Flask Server (Gunicorn + Nginx)] ---> [Telegram API] ---> [Your Phone/Desktop]

Setup and Installation
Follow these steps to get the bot running on your server.

1. Prerequisites
A server running a Linux distribution (this guide uses Ubuntu).

Python 3.8 or higher.

2. Clone the Repository
Get the project code onto your server:

git clone https://github.com/DaSpaceJesus/Woocommerce_webhook_telegram_bot
cd Woocommerce_webhook_telegram_bot

3. Create a Python Virtual Environment

python3 -m venv venv

Activate it

source venv/bin/activate

4. Install Dependencies

pip install -r requirements.txt

5. Create the Configuration File

Enter your credentials in config.ini file.

[TELEGRAM]
TOKEN = YOUR_TELEGRAM_BOT_API_TOKEN_HERE

CHAT_ID = CHAT_ID_1,CHAT_ID_2

TOKEN: Get this from the BotFather on Telegram.

CHAT_ID: The unique ID(s) of the user, group, or channel you want to send notifications to. For multiple chats, separate them with a comma. You can get a chat ID from a bot like @userinfobot.

6. Configure WooCommerce Webhook
In your WordPress dashboard, go to WooCommerce > Settings > Advanced > Webhooks.

Click "Add webhook".

Configure the settings:

Name: A descriptive name (e.g., "Telegram Order Bot").

Status: Set to Active.

Topic: Select Order Created.

Delivery URL: The URL of your server where the bot is listening. For example: http://your-domain.com/webhook or http://your-server-ip:port/webhook.

Secret: Leave blank unless you plan to implement signature verification.

Click "Save webhook".

## Bonus
Create a systemd Service: Write a service file to ensure the bot runs continuously and restarts automatically on failure or server reboot.

Secure with HTTPS: Use Certbot and Let's Encrypt to enable HTTPS on your domain, securing the data sent from WooCommerce.

Open ports on Server: allow used port on firewall and avoid using random ports. use known ones.
the port can be configured on last line of script.

### Make sure your virtual environment is active
source venv/bin/activate

### Run the Flask app
python telegram_webhook_bot.py

The server will start