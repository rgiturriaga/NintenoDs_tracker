import time
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

# Set up logger
logger = logging.getLogger(__name__)

class ProductScraper:
    """High-level scraper using Selenium to bypass bot detection.

    Attributes:
        target_url (str): The URL of the marketplace to scrape.
        firefox_options (Options): Headless Firefox browser configurations.
    """

    def __init__(self, target_url: str):
        """Initializes ProductScraper with a target URL and headless Firefox settings.

        Args:
            target_url (str): The target marketplace URL.
        """
        self.target_url = target_url
        self.firefox_options = Options()
        # Enable headless mode for Linux/CI execution environments
        self.firefox_options.add_argument("--headless") 
        self.firefox_options.set_preference(
            "general.useragent.override", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        )

    def fetch_page_content(self) -> str:
        """Opens a headless browser to render the page and get the HTML.

        Returns:
            str: The raw HTML content string of the loaded page, or None if it fails.
        """
        logger.info(f"Opening headless Firefox browser to: {self.target_url}")
        
        try:
            # Automatic driver installation & browser initialization
            driver = webdriver.Firefox(
                service=Service(GeckoDriverManager().install()), 
                options=self.firefox_options
            )
        except Exception as init_error:
            logger.error(f"Failed to initialize Firefox WebDriver: {init_error}", exc_info=True)
            return None

        try:
            driver.get(self.target_url)
            # Wait for JavaScript to load product listings
            time.sleep(5) 
            html = driver.page_source
            logger.info("Successfully fetched page source.")
            return html
        except Exception as fetch_error:
            logger.error(f"Error fetching page content via Selenium: {fetch_error}", exc_info=True)
            return None
        finally:
            # Ensure the browser is always quit to prevent process/RAM leakage
            driver.quit()
            logger.info("Firefox WebDriver closed.")

    def analyze_merca_libre(self, html_content: str) -> list:
        """Parses Mercado Libre product listings from HTML.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: A list of dictionaries, each containing 'name', 'price', and 'link'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Target the main product cards
        items = soup.find_all(['div', 'li'], class_=['poly-card', 'ui-search-result__wrapper'])

        for item in items:
            name_element = item.find('a', class_='poly-component__title') or item.find('h2')
            
            # Avoid picking up monthly installments or discount percentages
            price_container = item.find('div', class_='poly-price__current') or \
                              item.find('div', class_='ui-search-price__second-line')
            
            if price_container:
                price_element = price_container.find('span', class_='andes-money-amount__fraction')
            else:
                price_element = item.find('span', class_='andes-money-amount__fraction')

            link_element = item.find('a', href=True)

            if name_element and price_element:
                price_text = price_element.get_text().strip()
                products.append({
                    "name": name_element.get_text().strip(),
                    "price": price_text,
                    "link": link_element['href'] if link_element else self.target_url
                })
        
        return products

    def analyze_prices(self, html_content: str) -> list:
        """Generic fallback parser or placeholder for other marketplaces like eBay.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: Empty list (to be implemented with specific marketplace parser).
        """
        logger.warning("Generic analyze_prices called but not implemented yet.")
        return []