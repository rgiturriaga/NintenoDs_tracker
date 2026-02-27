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
        self.chrome_options = Options()
        # COMENTA ESTA LÍNEA PARA VER EL NAVEGADOR (Solo para pruebas)
        # self.chrome_options.add_argument("--headless") 
        self.chrome_options.add_argument("--no-sandbox")
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
        
        # 1. Buscamos primero todos los elementos que tienen el precio
        price_elements = soup.find_all('span', class_='andes-money-amount__fraction')

        for price_element in price_elements:
            # 2. Subimos al contenedor principal (el padre) de este precio
            # Usamos un try/except porque a veces el precio no tiene un padre con título
            try:
                # 'parents' nos permite subir niveles en el HTML hasta encontrar algo
                container = price_element.find_parent('div', class_='ui-search-result__wrapper') or \
                            price_element.find_parent('li')
                
                if container:
                    name = container.find(['h2', 'h3']) # Buscamos h2 o h3
                    link = container.find('a')
                    
                    if name and link:
                        products.append({
                            "name": name.get_text().strip(),
                            "price": price_element.get_text().strip(),
                            "link": link['href']
                        })
            except Exception:
                continue
        # Debug: ver qué está viendo el bot
        print("[DEBUG] Encabezados encontrados:")
        all_h2 = soup.find_all('h2')
        for i, h in enumerate(all_h2[:7]): # Imprimir solo los 7 primeros
            print(f"Header {i}: {h.get_text().strip()}")
        print(f"[*] Success! Found {len(products)} products using proximity search.")
        return products