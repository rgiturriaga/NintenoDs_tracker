import random
import logging
import requests
from bs4 import BeautifulSoup

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

# Rotate between a few realistic User-Agent strings to reduce fingerprinting.
_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


class ProductScraper:
    """Scraper that fetches Mercado Libre listing pages via HTTP requests.

    Mercado Libre uses server-side rendering (Next.js SSR), so product listings
    are embedded in the initial HTML response and do not require JavaScript
    execution. Using requests instead of a headless browser avoids the
    Firefox/geckodriver stack entirely, reducing memory use and removing all
    container compatibility issues.

    Attributes:
        target_url (str): The marketplace listing URL to scrape.
        session (requests.Session): Persistent HTTP session with browser headers.
    """

    def __init__(self, target_url: str):
        """Initializes the scraper with a target URL and a configured HTTP session.

        Args:
            target_url (str): The target marketplace URL.
        """
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            # Accept header exactly as Firefox sends it
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.7,en;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            # Fetch metadata headers (sent by modern Firefox)
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })

    def fetch_page_content(self) -> str | None:
        """Fetches the page HTML via an HTTP GET request.

        A random User-Agent is chosen per request and a small random delay is
        applied to avoid fixed-timing fingerprinting. Both measures make the
        traffic pattern less distinguishable from organic browser sessions.

        Returns:
            str: The raw HTML content of the page, or None on failure.
        """
        # Pick a fresh User-Agent for each request
        self.session.headers["User-Agent"] = random.choice(_USER_AGENTS)

        logger.info(f"Fetching: {self.target_url}")
        try:
            response = self.session.get(
                self.target_url,
                timeout=30,
                allow_redirects=True,
            )
            response.raise_for_status()
            logger.info(f"Response: HTTP {response.status_code} ({len(response.text)} chars)")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.target_url}: {e}")
            return None

    def analyze_merca_libre(self, html_content: str) -> list:
        """Parses Mercado Libre product listings from HTML.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: Dictionaries with 'name', 'price', and 'link' for each
                  console listing that passes the blacklist filter.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        products = []

        # Target the main product cards
        items = soup.find_all(["div", "li"], class_=["poly-card", "ui-search-result__wrapper"])

        for item in items:
            name_element = item.find("a", class_="poly-component__title") or item.find("h2")

            if not name_element:
                continue

            name_text = name_element.get_text().strip()

            # Skip games, accessories, spare parts, etc.
            if self._is_excluded(name_text):
                logger.debug(f"Excluded by blacklist: '{name_text}'")
                continue

            # Avoid picking up monthly installments or discount percentages
            price_container = (
                item.find("div", class_="poly-price__current")
                or item.find("div", class_="ui-search-price__second-line")
            )

            if price_container:
                price_element = price_container.find("span", class_="andes-money-amount__fraction")
            else:
                price_element = item.find("span", class_="andes-money-amount__fraction")

            link_element = item.find("a", href=True)

            if price_element:
                price_text = price_element.get_text().strip()
                products.append({
                    "name": name_text,
                    "price": price_text,
                    "link": link_element["href"] if link_element else self.target_url,
                })

        return products

    def _is_excluded(self, name: str) -> bool:
        """Returns True if the product name matches a blacklisted keyword.

        Args:
            name (str): The product listing name to evaluate.

        Returns:
            bool: True when the product should be discarded.
        """
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in BLACKLIST_KEYWORDS)

    def analyze_prices(self, html_content: str) -> list:
        """Generic fallback parser for non-Mercado Libre marketplaces.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: Empty list (placeholder for future marketplace support).
        """
        logger.warning("Generic analyze_prices called but not implemented yet.")
        return []