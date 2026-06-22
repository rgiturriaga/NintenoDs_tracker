# Nintendo DS Price Tracker: Developer Guide

This developer guide describes the architectural choices, security principles, resource lifecycle, and patterns to extend the codebase for new marketplaces.

---

## Design Patterns & Code Style

The project is structured with modular design principles:
- **Separation of Concerns**: [scraper.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/scraper.py) manages browser automation and parsing, [utils.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/utils.py) manages external API notification services, and [main.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/main.py) controls the configuration and monitoring loop execution.
- **Python Logging Standard**: Avoid raw `print` statements. Use `logging.getLogger(__name__)` with appropriate levels:
  - `INFO`: Execution milestones (monitoring cycles, found deals, webdriver closures).
  - `DEBUG`: Verbose product parsing logs and intermediate debugging fields.
  - `WARNING`: Recoverable errors (e.g. invalid config fallbacks, unrecognized HTML snippets).
  - `ERROR`: Unrecoverable execution errors or exceptions during an API dispatch.
- **Strict Linting & Style**: Follow Google Python style guidelines, documenting functions using structured parameters, exceptions, and return structures.

---

## Security by Design

To ensure this project is portfolio-safe:
1. **Decoupled Variables**: Configuration values and secrets are stored in a root [.env](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/.env) file. The code uses `load_dotenv` to read them via the system environment.
2. **Ignored Sensitive Assets**: The `.gitignore` matches `.env` and any local configuration caches to prevent accidental leaks.
3. **Safe Exception Tracebacks**: When API requests fail, the application does not print raw requests URLs containing API credentials to standard output. The URLs are hidden or sanitized.
4. **Timeouts**: Every HTTP post request has a set `timeout` parameter to avoid hanging threads indefinitely.

---

## Resource Lifecycle & Cleanups

Automated browsers can easily cause resource leaks if not cleaned up properly (especially on headless CLI setups).
- **Webdriver Terminations**: The `fetch_page_content` method wraps the webdriver lifecycle in a `try...finally` block. Regardless of network dropouts or BeautifulSoup parsing exceptions, `driver.quit()` is guaranteed to execute, terminating the browser process.
- **TCP Connection Reuse**: Instead of recreating TCP handshakes on every Telegram push, `utils.py` holds a persistent `requests.Session` object at the module level. This enables HTTP keep-alive connection reuse, significantly reducing notification latency and system sockets consumption.

---

## Extending the Scraper

To add support for a new marketplace (e.g., eBay or Amazon):

1. **Implement Parsing Logic**:
   Add a method inside `ProductScraper` class in [scraper.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/scraper.py) to parse the specific markup structure of the target website:
   ```python
   def analyze_ebay(self, html_content: str) -> list:
       soup = BeautifulSoup(html_content, 'html.parser')
       products = []
       # ... Add parsing tags ...
       return products
   ```
2. **Update Monitoring Flow**:
   Modify the main loop inside `run_price_monitor` in [main.py](file:///home/devil_hayabusa/Proyects/NintenoDs_tracker/src/main.py#L42):
   ```python
   if "mercadolibre" in target_url:
       products = scraper.analyze_merca_libre(html_content)
   elif "ebay" in target_url:
       products = scraper.analyze_ebay(html_content)
   else:
       products = scraper.analyze_prices(html_content)
   ```
3. **Create Tests**:
   Create a test cases suite in `tests/test_scraper.py` using mock HTML to test the parsing logic and verify it extracts the correct products list without opening real browsers.
