# Nintendo DS Price Tracker

A professional web scraping tool designed to monitor online marketplaces for affordable Nintendo DS consoles and send real-time alerts via Telegram.

## Tech Stack

- **Language:** Python 3.x
- **Libraries:** BeautifulSoup4, Requests, Python-dotenv
- **Automation:** Telegram Bot API
- **Version Control:** Git & GitHub

## Features

- Automated web scraping of product listings.
- HTML parsing to extract pricing and product titles.
- Environment variable management for sensitive credentials.
- Instant Telegram notifications for found deals.

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```powershell
   git clone [https://github.com/DevilHayabusa/nintendo-ds-tracker.git](https://github.com/DevilHayabusa/nintendo-ds-tracker.git)
   cd nintendo-ds-tracker

2. Create and activate a virtual environment:
python -m venv venv
.\venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Configure Environment Variables:
Create a .env file in the root directory and add your credentials:
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TARGET_URL=your_target_marketplace_url