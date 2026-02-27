import time
from scraper import ProductScraper
from utils import send_telegram_alert

def run_price_monitor():
    """
    Main execution function to monitor prices and notify via Telegram.
    """
    # 1. Configuration: Change this URL to switch between eBay or Mercado Libre
    target_url = "https://listado.mercadolibre.com.mx/nintendo-ds-lite"
    max_price = 1000.0 # Budget in your local currency
    check_interval = 3600 

    print(f"[*] Starting monitor for: {target_url}")
    scraper = ProductScraper(target_url)

    while True:
        print("[*] Checking for new deals...")
        html_content = scraper.fetch_page_content()

        if html_content:
            # 2. SELECT THE ANALYZER BASED ON THE URL
            # This is the specific logic you asked about:
            if "mercadolibre" in target_url:
                products = scraper.analyze_merca_libre(html_content)
            else:
                # Default to eBay logic if it's not Mercado Libre
                products = scraper.analyze_prices(html_content)
            
            # 3. Process the results
            for product in products:
                try:
                    # Clean the price string (handle decimals and currency symbols)
                    clean_price = product['price'].replace('$', '').replace(',', '').strip()
                    current_price = float(clean_price)
                    print(f"[DEBUG] Found: {product['name']} at ${current_price}")
                    if current_price <= max_price:
                        # Using HTML tags instead of Markdown
                        message = (
                            f"<b>🎮 New Deal Found!</b>\n\n"
                            f"Product: {product['name']}\n"
                            f"Price: ${current_price}\n"
                            f"Link: {product.get('link', target_url)}"
                        )
                        send_telegram_alert(message)
                        print(f"[!] Alert sent: {product['name']} at ${current_price}")
                        
                except (ValueError, KeyError):
                    continue

        print(f"[*] Sleeping for {check_interval} seconds...")
        time.sleep(check_interval)

if __name__ == "__main__":
    run_price_monitor()