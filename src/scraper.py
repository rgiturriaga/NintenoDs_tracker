import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

# Set up logger
logger = logging.getLogger(__name__)

# Words that identify non-console listings (games, accessories, spare parts).
# Any product whose name contains one of these terms is discarded.
BLACKLIST_KEYWORDS: frozenset[str] = frozenset({
    # Games / software
    "juego", "game", "games", "cartucho", "cartridge", "rom",
    # Accessories / cases
    "accesorio", "funda", "estuche", "bolsa", "mochila",
    "case", "bag", "protector", "cover", "skin",
    # Chargers / cables
    "cargador", "charger", "cable", "adaptador", "adapter", "fuente",
    # Spare parts / repairs
    "repuesto", "refaccion", "pantalla", "screen", "lcd",
    "bateria", "battery", "boton", "button", "bisagra", "hinge",
    "bocina", "speaker", "microfono", "microphone",
    # Stylus
    "stylus", "lapiz", "lapicero",
    # Documentation
    "manual", "instrucciones",
})

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
        # Prevent Firefox from looking for an existing instance to reuse.
        # In a container each scan spawns a fresh process; without this flag
        # Firefox may hang trying to contact a non-existent prior session.
        self.firefox_options.add_argument("-no-remote")
        self.firefox_options.set_preference(
            "general.useragent.override", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        )
        # Disable Firefox's internal multi-process content sandbox.
        # In a hardened container (cap_drop: ALL, read_only filesystem) the
        # sandbox requires kernel capabilities we intentionally do not grant.
        # The Docker container itself is the security boundary.
        self.firefox_options.set_preference("security.sandbox.content.level", 0)
        self.firefox_options.set_preference("security.sandbox.gpu.level", 0)
        # Disable GPU hardware acceleration. Containers have no real GPU and the
        # GPU compositor process crashes silently, which surfaces as a marionette
        # decode error. Software rendering is slower but stable in headless mode.
        self.firefox_options.set_preference("layers.acceleration.disabled", True)
        self.firefox_options.set_preference("webgl.disabled", True)
        self.firefox_options.set_preference("media.hardware-video-decoding.enabled", False)
        # Hide the navigator.webdriver property that anti-bot systems (e.g. Akamai)
        # check to detect Selenium-controlled browsers. This makes the session
        # look indistinguishable from a regular manual browsing session.
        self.firefox_options.set_preference("dom.webdriver.enabled", False)
        self.firefox_options.set_preference("useAutomationExtension", False)

    def fetch_page_content(self) -> str:
        """Opens a headless browser to render the page and get the HTML.

        Returns:
            str: The raw HTML content string of the loaded page, or None if it fails.
        """
        logger.info(f"Opening headless Firefox browser to: {self.target_url}")
        
        try:
            # If a pre-installed geckodriver is available (e.g. inside Docker), use it
            # directly to avoid a network download at startup. Fall back to
            # webdriver_manager for local development environments.
            gecko_path = os.getenv("GECKODRIVER_PATH")
            service = Service(gecko_path) if gecko_path else Service(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=self.firefox_options)
        except Exception as init_error:
            logger.error(f"Failed to initialize Firefox WebDriver: {init_error}", exc_info=True)
            return None

        try:
            driver.get(self.target_url)
            # Wait a randomized amount of time for JS to render product listings.
            # A fixed delay (e.g. always 5s) creates a detectable timing fingerprint;
            # a human never loads pages at perfectly consistent intervals.
            wait_seconds = random.uniform(4.0, 9.0)
            logger.debug(f"Waiting {wait_seconds:.1f}s for page JS to render...")
            time.sleep(wait_seconds)
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

            if not name_element:
                continue

            name_text = name_element.get_text().strip()

            # Skip games, accessories, spare parts, etc.
            if self._is_excluded(name_text):
                logger.debug(f"Excluded by blacklist: '{name_text}'")
                continue

            # Avoid picking up monthly installments or discount percentages
            price_container = (
                item.find('div', class_='poly-price__current')
                or item.find('div', class_='ui-search-price__second-line')
            )

            if price_container:
                price_element = price_container.find('span', class_='andes-money-amount__fraction')
            else:
                price_element = item.find('span', class_='andes-money-amount__fraction')

            link_element = item.find('a', href=True)

            if price_element:
                price_text = price_element.get_text().strip()
                products.append({
                    "name": name_text,
                    "price": price_text,
                    "link": link_element['href'] if link_element else self.target_url,
                })

        return products

    def _is_excluded(self, name: str) -> bool:
        """Returns True if the product name matches a blacklisted keyword.

        Args:
            name (str): The product listing name to evaluate.

        Returns:
            bool: True when the product should be discarded, False when it can pass.
        """
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in BLACKLIST_KEYWORDS)

    def analyze_prices(self, html_content: str) -> list:
        """Generic fallback parser or placeholder for other marketplaces like eBay.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: Empty list (to be implemented with specific marketplace parser).
        """
        logger.warning("Generic analyze_prices called but not implemented yet.")
        return []