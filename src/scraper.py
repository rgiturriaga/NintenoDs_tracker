import random
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Words that identify non-console listings (games, accessories, spare parts).
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

# Rotate between realistic User-Agent strings to avoid fixed fingerprinting.
_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


class ProductScraper:
    """Scraper that fetches Mercado Libre listing pages via HTTP requests.

    brotlicffi must be installed so that urllib3 can automatically decompress
    the brotli-encoded responses that Mercado Libre returns. Without it,
    response.text contains raw compressed bytes that BeautifulSoup cannot parse.

    Attributes:
        target_url (str): The marketplace listing URL to scrape.
        session (requests.Session): Persistent HTTP session with browser headers.
    """

    def __init__(self, target_url: str):
        """Initializes the scraper with a target URL and a browser-like session.

        Args:
            target_url (str): The target marketplace URL.
        """
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en-US;q=0.7,en;q=0.6",
            # 'br' is safe here because brotlicffi is installed and urllib3
            # detects it automatically to decompress brotli responses.
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })

    def fetch_listings(self) -> list:
        """Public interface: fetches the page and returns filtered products.

        Returns:
            list: Dictionaries with 'name', 'price', and 'link'.
        """
        html = self._fetch_page_content()
        if not html:
            return []
        return self._analyze_merca_libre(html)

    def _fetch_page_content(self) -> str | None:
        """Fetches the page HTML via an HTTP GET request.

        brotlicffi enables automatic brotli decompression in urllib3, so
        response.text always returns a valid UTF-8 string regardless of
        the Content-Encoding the server chose.

        Returns:
            str: The raw HTML content of the page, or None on failure.
        """
        self.session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        logger.info(f"Fetching: {self.target_url}")
        try:
            response = self.session.get(
                self.target_url,
                timeout=30,
                allow_redirects=True,
            )
            response.raise_for_status()
            logger.info(
                f"Response: HTTP {response.status_code} "
                f"({len(response.text)} chars, "
                f"encoding={response.headers.get('content-encoding', 'none')})"
            )
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.target_url}: {e}")
            return None

    def _analyze_merca_libre(self, html_content: str) -> list:
        """Parses Mercado Libre product listings from HTML.

        Tries CSS selector strategies from newest to oldest since the SSR
        markup may differ from the JS-hydrated version.

        Args:
            html_content (str): The raw HTML page source.

        Returns:
            list: Filtered product dictionaries.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Log first 400 chars to identify page structure in docker logs.
        snippet = " ".join(html_content[:400].split())
        logger.info(f"HTML preview: {snippet}")

        # Strategy 1: poly-card / ui-search-result__wrapper (2024+ structure).
        # Two separate calls combined with + to get OR behaviour without lambdas.
        items = soup.find_all(["div", "li"], class_="poly-card")
        items += soup.find_all(["div", "li"], class_="ui-search-result__wrapper")
        logger.info(f"Strategy 1 (poly-card): {len(items)} item(s)")

        if not items:
            # Strategy 2: classic SSR layout item
            items = soup.find_all("li", class_="ui-search-layout__item")
            logger.info(f"Strategy 2 (layout__item): {len(items)} item(s)")

        if not items:
            # Strategy 3: CSS attribute substring selector — matches any element
            # whose class attribute contains the text 'ui-search-result'.
            items = soup.select("[class*='ui-search-result']")
            logger.info(f"Strategy 3 (ui-search-result*): {len(items)} item(s)")

        if not items:
            logger.warning(
                f"No items found in {len(html_content)} chars. "
                "Page may be bot-detected or HTML structure changed."
            )
            return []

        products = []
        for item in items:
            name_element = (
                item.find("a", class_="poly-component__title")
                or item.find("a", class_="ui-search-item__title-label")
                or item.find("h2", class_="ui-search-item__title")
                or item.find("h2")
            )
            if not name_element:
                continue

            name_text = name_element.get_text().strip()
            if self._is_excluded(name_text):
                logger.debug(f"Excluded by blacklist: '{name_text}'")
                continue

            price_element = (
                item.find("span", class_="andes-money-amount__fraction")
                or item.find("span", class_="price-tag-fraction")
            )
            link_element = item.find("a", href=True)

            if price_element:
                products.append({
                    "name": name_text,
                    "price": price_element.get_text().strip(),
                    "link": link_element["href"] if link_element else self.target_url,
                })

        return products

    def _is_excluded(self, name: str) -> bool:
        """Returns True if the product name matches a blacklisted keyword."""
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in BLACKLIST_KEYWORDS)