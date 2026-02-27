import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_telegram_alert(message):
    """
    Sends a notification message to a specific Telegram chat.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Error: Telegram credentials not found in environment variables.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Failed to send Telegram message: {error}")