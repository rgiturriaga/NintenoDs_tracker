import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logger
logger = logging.getLogger(__name__)

# Persistent connection pool session for resource optimization
_session = requests.Session()

def send_telegram_alert(message: str) -> dict:
    """Sends a notification message to a specific Telegram chat with error handling.

    Args:
        message (str): The HTML or plain text formatted message to send.

    Returns:
        dict: The JSON response dictionary from Telegram API on success, or None on failure.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        logger.error("Telegram credentials not found in environment variables.")
        return None

    # Construct url safely
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        logger.info("Sending alert notification to Telegram...")
        response = _session.post(url, data=payload, timeout=10)
        
        # If it fails, log details securely without exposing credentials
        if response.status_code != 200:
            logger.error(
                f"Telegram API Error: Status {response.status_code}. "
                f"Response body: {response.text}"
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        logger.error(f"Failed to send Telegram message: {error}")
        return None