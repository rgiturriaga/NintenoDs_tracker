import pytest
from bs4 import BeautifulSoup

from scraper import ProductScraper

# Mock HTML content resembling Mercado Libre product listings
MOCK_MERCADO_LIBRE_HTML = """
<html>
  <body>
    <!-- Valid product card using new class structure -->
    <div class="poly-card">
      <a class="poly-component__title" href="https://articulo.mercadolibre.com.mx/MLM-123">Nintendo DS Lite Coral</a>
      <div class="poly-price__current">
        <span class="andes-money-amount__fraction">850</span>
      </div>
    </div>

    <!-- Valid product card using alternative class structure -->
    <li class="ui-search-result__wrapper">
      <h2>Consola Nintendo DSi XL</h2>
      <div class="ui-search-price__second-line">
        <span class="andes-money-amount__fraction">1,200</span>
      </div>
      <a href="https://articulo.mercadolibre.com.mx/MLM-456">Link to item</a>
    </li>

    <!-- Malformed product card with missing price -->
    <div class="poly-card">
      <a class="poly-component__title" href="https://articulo.mercadolibre.com.mx/MLM-789">Broken Nintendo DS</a>
      <div class="poly-price__current">
        <!-- Missing price element class -->
      </div>
    </div>
  </body>
</html>
"""

def test_analyze_merca_libre():
    """Test that Mercado Libre parser correctly extracts products, names, and clean prices."""
    scraper = ProductScraper("https://listado.mercadolibre.com.mx/nintendo-ds")
    products = scraper.analyze_merca_libre(MOCK_MERCADO_LIBRE_HTML)

    # We expect exactly 2 valid products (since the 3rd one has no price fraction)
    assert len(products) == 2

    # Check first item (new card classes)
    assert products[0]["name"] == "Nintendo DS Lite Coral"
    assert products[0]["price"] == "850"
    assert products[0]["link"] == "https://articulo.mercadolibre.com.mx/MLM-123"

    # Check second item (alternative classes and comma in price)
    assert products[1]["name"] == "Consola Nintendo DSi XL"
    assert products[1]["price"] == "1,200"
    assert products[1]["link"] == "https://articulo.mercadolibre.com.mx/MLM-456"

def test_analyze_prices_fallback():
    """Test that the fallback generic parser returns an empty list and behaves gracefully."""
    scraper = ProductScraper("https://www.ebay.com/nintendo-ds")
    products = scraper.analyze_prices("<html></html>")
    assert products == []

def test_fetch_page_content_mocked(mocker):
    """Test that fetch_page_content behaves correctly with driver mock, preventing real browser opens."""
    # Mock the webdriver.Firefox instance and its return value
    mock_driver_instance = mocker.MagicMock()
    mock_driver_instance.page_source = "<html>Mock Source</html>"
    
    mock_webdriver = mocker.patch("selenium.webdriver.Firefox", return_value=mock_driver_instance)
    mock_manager = mocker.patch("webdriver_manager.firefox.GeckoDriverManager.install", return_value="/mock/path/geckodriver")
    
    scraper = ProductScraper("https://listado.mercadolibre.com.mx/nintendo-ds")
    html = scraper.fetch_page_content()
    
    # Assert driver was invoked and quit was called
    mock_webdriver.assert_called_once()
    mock_driver_instance.get.assert_called_once_with("https://listado.mercadolibre.com.mx/nintendo-ds")
    mock_driver_instance.quit.assert_called_once()
    assert html == "<html>Mock Source</html>"

def test_fetch_page_content_exception(mocker):
    """Test that fetch_page_content handles exceptions gracefully and closes the browser."""
    mock_driver_instance = mocker.MagicMock()
    mock_driver_instance.get.side_effect = Exception("Network timeout")
    
    mocker.patch("selenium.webdriver.Firefox", return_value=mock_driver_instance)
    mocker.patch("webdriver_manager.firefox.GeckoDriverManager.install", return_value="/mock/path/geckodriver")
    
    scraper = ProductScraper("https://listado.mercadolibre.com.mx/nintendo-ds")
    html = scraper.fetch_page_content()
    
    # Assert driver quit was still called in the finally block, and html is None
    mock_driver_instance.quit.assert_called_once()
    assert html is None
