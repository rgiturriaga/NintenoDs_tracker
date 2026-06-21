import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup

class ProductScraper:
    """
    High-level scraper using Selenium to bypass bot detection.
    """
    def __init__(self, target_url):
        self.target_url = target_url
        self.firefox_options = Options()
        # ENABLE HEADLESS MODE FOR ARCH LINUX
        self.firefox_options.add_argument("--headless") 
        self.firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0")

    def fetch_page_content(self):
        """
        Opens a real browser to render the page and get the HTML.
        """
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=self.firefox_options)
        try:
            print(f"[*] Opening browser to: {self.target_url}")
            driver.get(self.target_url)
            # Wait 5 seconds for JavaScript to load products
            time.sleep(5) 
            html = driver.page_source
            return html
        except Exception as error:
            print(f"Error with Selenium: {error}")
            return None
        finally:
            driver.quit() # Always close the browser to save RAM

    def analyze_merca_libre(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Target the main product cards
        items = soup.find_all(['div', 'li'], class_=['poly-card', 'ui-search-result__wrapper'])

        for item in items:
            name_element = item.find('a', class_='poly-component__title') or item.find('h2')
            
            # CRITICAL FIX: We look specifically for the metadata price container
            # This avoids picking up 'monthly installments' or 'discount percentages'
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
                    "link": link_element['href'] if link_element else "No link"
                })
        
        return products