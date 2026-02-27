import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class ProductScraper:
    """
    High-level scraper using Selenium to bypass bot detection.
    """
    def __init__(self, target_url):
        self.target_url = target_url
        
        # Configure Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless") # Run without opening a window
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    def fetch_page_content(self):
        """
        Opens a real browser to render the page and get the HTML.
        """
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
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
        
        # New 2026 generic selectors
        items = soup.select('li.ui-search-layout__item')

        for item in items:
            name = item.find('h2')
            price = item.find('span', class_='andes-money-amount__fraction')
            link = item.find('a')

            if name and price:
                products.append({
                    "name": name.get_text().strip(),
                    "price": price.get_text().strip(),
                    "link": link['href'] if link else "No link"
                })
        
        print(f"[*] Success! Found {len(products)} products using Selenium.")
        return products