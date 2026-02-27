import time
from scraper import ProductScraper
from utils import send_telegram_alert

def run_price_monitor():
    """
    Main execution function to monitor prices and notify via Telegram.
    """
    # Configuration
    target_url = "https://www.ebay.com/sch/i.html?_nkw=nintendo+ds+lite+console"
    max_price = 50.0  # Set your budget here
    check_interval = 3600  # Time in seconds (1 hour)

    print(f"[*] Starting monitor for Nintendo DS under ${max_price}...")
    
    scraper = ProductScraper(target_url)

    while True:
        print("[*] Checking for new deals...")
        html_content = scraper.fetch_page_content()

        if html_content:
            products = scraper.analyze_prices(html_content)
            
            for product in products:
                # Basic price cleaning (removing symbols like $ or ,)
                try:
                    price_str = product['price'].replace('$', '').replace(',', '').split(' ')[0]
                    current_price = float(price_str)
                    
                    if current_price <= max_price:
                        message = (
                            f"🎮 **New Nintendo DS Deal Found!**\n\n"
                            f"Product: {product['name']}\n"
                            f"Price: ${current_price}\n"
                            f"Link: {target_url}"
                        )
                        send_telegram_alert(message)
                        print(f"[!] Alert sent for: {product['name']} at ${current_price}")
                        
                except ValueError:
                    # Skip items where price cannot be parsed correctly
                    continue

        # Wait before the next check to avoid being banned
        print(f"[*] Sleeping for {check_interval} seconds...")
        time.sleep(check_interval)

if __name__ == "__main__":
    run_price_monitor()