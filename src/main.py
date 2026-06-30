import os
import time
import random
import logging
import datetime
import threading
from dotenv import load_dotenv
from scraper import ProductScraper
from utils import send_telegram_alert

load_dotenv()

logger = logging.getLogger(__name__)


def _next_scan_datetime(window_start_h: int, window_end_h: int) -> datetime.datetime:
    """Returns a random datetime within today's (or tomorrow's) scan window.

    Picks a uniformly random minute inside [window_start_h, window_end_h).
    If the chosen time for today has already passed, it reschedules for tomorrow
    with a fresh random offset so the pattern is never the same two days in a row.

    Args:
        window_start_h (int): Window open hour, 0-23 (e.g. 0 for midnight).
        window_end_h (int): Window close hour, 0-23 exclusive (e.g. 17 for 5 PM).

    Returns:
        datetime.datetime: Next datetime at which a scan should run.
    """
    now = datetime.datetime.now()
    total_window_minutes = (window_end_h - window_start_h) * 60

    def random_moment_on(date: datetime.date) -> datetime.datetime:
        offset = datetime.timedelta(minutes=random.randint(0, total_window_minutes - 1))
        window_open = datetime.datetime.combine(date, datetime.time(hour=window_start_h))
        return window_open + offset

    candidate = random_moment_on(now.date())
    if candidate > now:
        return candidate

    # Today's window has fully elapsed; pick a fresh random time for tomorrow.
    return random_moment_on((now + datetime.timedelta(days=1)).date())


def run_monitor_loop(stop_event: threading.Event, config: dict) -> None:
    """Price monitoring loop. Runs until stop_event is set.

    Schedules exactly one scan per day at a random time within the configured
    window. The next scan time is stored in config['next_scan_at'] so the
    Telegram /status command can display it.

    Args:
        stop_event (threading.Event): Set this from outside to stop the loop cleanly.
        config (dict): Runtime configuration with keys:
            - target_url (str)
            - max_price (float)
            - scan_window_start (int): Window open hour  (default 0  = midnight)
            - scan_window_end   (int): Window close hour (default 17 = 5 PM)
    """
    target_url    = config.get("target_url", "https://listado.mercadolibre.com.mx/nintendo-ds-lite")
    max_price     = config.get("max_price", 1000.0)
    window_start  = config.get("scan_window_start", 0)
    window_end    = config.get("scan_window_end", 17)

    logger.info(
        f"Monitor started: {target_url} | max ${max_price} "
        f"| daily window {window_start:02d}:00 - {window_end:02d}:00"
    )
    scraper = ProductScraper(target_url)

    while not stop_event.is_set():
        # --- Schedule next scan ---
        next_dt = _next_scan_datetime(window_start, window_end)
        config["next_scan_at"] = next_dt
        wait_seconds = max(0, (next_dt - datetime.datetime.now()).total_seconds())
        logger.info(
            f"Next scan scheduled at {next_dt.strftime('%Y-%m-%d %H:%M')} "
            f"(sleeping {int(wait_seconds)}s)."
        )

        # Sleep until then; wakes immediately if stop_event is set.
        stop_event.wait(timeout=wait_seconds)
        if stop_event.is_set():
            break

        # --- Run scan ---
        config["next_scan_at"] = None
        logger.info("Scan started.")

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
            logger.error(f"Unexpected error during scan: {e}", exc_info=True)

    logger.info("Monitor loop stopped cleanly.")


if __name__ == "__main__":
    # Standalone mode: runs the monitor directly without the Telegram bot.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )

    config = {
        "target_url":        os.getenv("TARGET_URL", "https://listado.mercadolibre.com.mx/nintendo-ds-lite"),
        "max_price":         float(os.getenv("MAX_PRICE", "1000.0")),
        "scan_window_start": int(os.getenv("SCAN_WINDOW_START", "0")),
        "scan_window_end":   int(os.getenv("SCAN_WINDOW_END", "17")),
    }

    stop_event = threading.Event()
    run_monitor_loop(stop_event, config)