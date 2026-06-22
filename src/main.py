import os
import time
import logging
from dotenv import load_dotenv
from scraper import ProductScraper
from utils import send_telegram_alert

# Load env variables
load_dotenv()

# Configure standard logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def run_price_monitor():
    """Main execution loop that monitors listings and notifies via Telegram.

    Retrieves targets and budget configuration from the environment, uses
    ProductScraper to parse listings, and posts alerts via Telegram when price matches.
    """
    # Load configuration from environment variables with safe fallbacks
    target_url = os.getenv("TARGET_URL", "https://listado.mercadolibre.com.mx/nintendo-ds-lite")
    
    try:
        max_price = float(os.getenv("MAX_PRICE", "1000.0"))
    except ValueError:
        logger.warning("Invalid MAX_PRICE in .env, falling back to 1000.0")
        max_price = 1000.0

    try:
        check_interval = int(os.getenv("CHECK_INTERVAL", "3600"))
    except ValueError:
        logger.warning("Invalid CHECK_INTERVAL in .env, falling back to 3600")
        check_interval = 3600

    logger.info(f"Starting price monitor for: {target_url} (Max Price: ${max_price})")
    scraper = ProductScraper(target_url)

    while True:
        logger.info("Checking for new deals...")
        try:
            html_content = scraper.fetch_page_content()

            if html_content:
                # Select parser based on target site
                if "mercadolibre" in target_url:
                    products = scraper.analyze_merca_libre(html_content)
                else:
                    products = scraper.analyze_prices(html_content)
                
                logger.info(f"Processed {len(products)} listings from page.")
                
                # Analyze prices and trigger alerts
                for product in products:
                    try:
                        clean_price = product['price'].replace('$', '').replace(',', '').strip()
                        current_price = float(clean_price)
                        logger.debug(f"Found: '{product['name']}' at ${current_price}")
                        
                        if current_price <= max_price:
                            message = (
                                f"<b>🎮 New Deal Found!</b>\n\n"
                                f"Product: {product['name']}\n"
                                f"Price: ${current_price}\n"
                                f"Link: {product.get('link', target_url)}"
                            )
                            send_telegram_alert(message)
                            logger.info(f"Alert sent: '{product['name']}' at ${current_price}")
                            
                    except (ValueError, KeyError) as e:
                        logger.debug(f"Skipping product parsing line due to error: {e}")
                        continue
            else:
                logger.warning("Could not fetch page content in this cycle.")
        except Exception as e:
            logger.error(f"Unexpected error in monitor loop: {e}", exc_info=True)

        logger.info(f"Sleeping for {check_interval} seconds...")
        time.sleep(check_interval)

if __name__ == "__main__":
    run_price_monitor()