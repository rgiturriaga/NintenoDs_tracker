import logging
import requests
from urllib.parse import urlparse

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

# Mercado Libre public search API — no authentication required.
# Site ID for Mexico is MLM.
_ML_API_URL = "https://api.mercadolibre.com/sites/MLM/search"


class ProductScraper:
    """Scraper backed by the official Mercado Libre public search API.

    The API returns structured JSON directly, bypassing all HTML scraping
    and bot-detection (Akamai) that blocks plain HTTP requests to the
    listing pages. No browser is needed.

    Attributes:
        target_url (str): The original listing URL (kept for logging/links).
        search_query (str): Search term derived from the URL path.
    """

    def __init__(self, target_url: str):
        """Initializes the scraper, deriving the search query from the URL.

        The URL path segment is used as the search query so that the existing
        .env TARGET_URL values continue to work without any changes:
            https://listado.mercadolibre.com.mx/nintendo-ds  ->  "nintendo ds"
            https://listado.mercadolibre.com.mx/nintendo-3ds ->  "nintendo 3ds"

        Args:
            target_url (str): The marketplace listing URL from configuration.
        """
        self.target_url = target_url
        # Extract the last path segment and convert hyphens to spaces
        path_segment = urlparse(target_url).path.strip("/").split("/")[-1]
        self.search_query = path_segment.replace("-", " ")

    def fetch_listings(self) -> list:
        """Searches Mercado Libre via the public API and returns filtered products.

        Makes a single GET request to the ML API with the derived search query.
        Results are filtered by the blacklist before being returned. Price
        filtering happens in main.py after all URLs have been aggregated.

        Returns:
            list: Dictionaries with 'name', 'price' (string), and 'link'
                  for each console listing that passes the blacklist filter.
                  Returns an empty list on network errors or no results.
        """
        logger.info(f"API search for: '{self.search_query}'")
        try:
            response = requests.get(
                _ML_API_URL,
                params={"q": self.search_query, "limit": 48},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"ML API request failed for '{self.search_query}': {e}")
            return []

        raw_items = data.get("results", [])
        logger.info(f"API returned {len(raw_items)} raw item(s)")

        products = []
        for item in raw_items:
            title = item.get("title", "")
            price = item.get("price")

            if price is None:
                continue
            if self._is_excluded(title):
                logger.debug(f"Excluded by blacklist: '{title}'")
                continue

            products.append({
                "name": title,
                # Store as integer string so main.py price parsing stays the same
                "price": str(int(price)),
                "link": item.get("permalink", self.target_url),
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