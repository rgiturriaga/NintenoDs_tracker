import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_telegram_alert(message):
    """
    Sends a notification message to a specific Telegram chat with error handling.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Error: Telegram credentials not found.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # We simplify the message to avoid Markdown errors for now
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" # Switching to HTML is often more stable than Markdown
    }

    try:
        response = requests.post(url, data=payload)
        # If it fails, let's see the exact reason from Telegram
        if response.status_code != 200:
            print(f"Telegram API Error: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Failed to send Telegram message: {error}")