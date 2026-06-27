import os
import time
import logging
import threading
from dotenv import load_dotenv
from scraper import ProductScraper
from utils import send_telegram_alert

load_dotenv()

logger = logging.getLogger(__name__)


def run_monitor_loop(stop_event: threading.Event, config: dict) -> None:
    """Price monitoring loop. Runs until stop_event is set.

    Args:
        stop_event (threading.Event): Set this event from the outside to stop the loop cleanly.
        config (dict): Runtime configuration with keys:
            - target_url (str)
            - max_price (float)
            - check_interval (int): seconds between scans
    """
    target_url = config.get("target_url", "https://listado.mercadolibre.com.mx/nintendo-ds-lite")
    max_price = config.get("max_price", 1000.0)
    check_interval = config.get("check_interval", 3600)

    logger.info(f"Monitor started: {target_url} | max ${max_price} | every {check_interval}s")
    scraper = ProductScraper(target_url)

    while not stop_event.is_set():
        logger.info("Checking for new deals...")
        try:
            html_content = scraper.fetch_page_content()

            if html_content:
                if "mercadolibre" in target_url:
                    products = scraper.analyze_merca_libre(html_content)
                else:
                    products = scraper.analyze_prices(html_content)

                logger.info(f"Processed {len(products)} console listings after filtering.")

                for product in products:
                    try:
                        clean_price = product["price"].replace("$", "").replace(",", "").strip()
                        current_price = float(clean_price)
                        logger.debug(f"Found: '{product['name']}' at ${current_price}")

                        if current_price <= max_price:
                            message = (
                                f"<b>New Deal Found!</b>\n\n"
                                f"Product: {product['name']}\n"
                                f"Price: ${current_price:,.2f}\n"
                                f"Link: {product.get('link', target_url)}"
                            )
                            send_telegram_alert(message)
                            logger.info(f"Alert sent: '{product['name']}' at ${current_price}")

                    except (ValueError, KeyError) as e:
                        logger.debug(f"Skipping product due to parse error: {e}")
                        continue
            else:
                logger.warning("Could not fetch page content in this cycle.")

        except Exception as e:
            logger.error(f"Unexpected error in monitor loop: {e}", exc_info=True)

        # Wait for the next cycle. Using stop_event.wait() instead of time.sleep()
        # means the thread responds to a stop signal immediately without waiting
        # out the entire check_interval.
        logger.info(f"Sleeping for {check_interval}s (stop event will wake this up early).")
        stop_event.wait(timeout=check_interval)

    logger.info("Monitor loop stopped cleanly.")


if __name__ == "__main__":
    # Standalone mode: runs the monitor directly without the Telegram bot.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    config = {
        "target_url": os.getenv("TARGET_URL", "https://listado.mercadolibre.com.mx/nintendo-ds-lite"),
        "max_price": float(os.getenv("MAX_PRICE", "1000.0")),
        "check_interval": int(os.getenv("CHECK_INTERVAL", "3600")),
    }

    stop_event = threading.Event()
    run_monitor_loop(stop_event, config)