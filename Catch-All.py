import datetime
import json
from flask import Flask, request

# --- Flask App Initialization ---
app = Flask(__name__)

# --- The file where all webhook data will be logged ---
LOG_FILE = 'webhook_log.txt'


@app.route('/debug-webhook', methods=['POST'])
def webhook_data_catcher():
    """
    This endpoint catches all incoming POST requests,
    logs their headers and JSON body to a file, and returns a success message.
    """

    # Get the current timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Get the JSON data from the request
    try:
        data = request.get_json()
    except Exception as e:
        # If the request doesn't contain valid JSON, log the raw data instead
        data = {'error': 'Could not parse JSON', 'raw_data': request.get_data(as_text=True)}

    # Get the headers from the request
    headers = dict(request.headers)

    # --- Logging the received data to a file ---
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"--- Webhook Received at {timestamp} ---\n\n")

            # Log Headers
            f.write("[HEADERS]\n")
            # Pretty print headers using json.dumps for readability
            f.write(json.dumps(headers, indent=2))
            f.write("\n\n")

            # Log JSON Body
            f.write("[BODY]\n")
            # Pretty print the JSON payload
            f.write(json.dumps(data, indent=2))
            f.write("\n\n----------------------------------------\n\n")

        print(f"[{timestamp}] Successfully logged a webhook to {LOG_FILE}")

    except Exception as e:
        print(f"[{timestamp}] CRITICAL: Failed to write to log file {LOG_FILE}. Error: {e}")
        # Return a server error if we can't even write the log
        return "Internal Server Error: Could not write to log file.", 500

    # Let WooCommerce know that we received the webhook successfully
    return "Webhook data received and logged.", 200


if __name__ == '__main__':
    # You can change the port if needed.
    # Make sure this port is open on your server's firewall.
    print("Starting webhook debugger server...")
    print(f"Listening for POST requests on http://0.0.0.0:4430/debug-webhook")
    print(f"Data will be saved to '{LOG_FILE}'")
    app.run(host='0.0.0.0', port=4430)
