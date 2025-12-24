"""
Optional: Selenium-based scraper for JavaScript-heavy sites
Install: pip install selenium webdriver-manager
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
from config import Config

class SeleniumScraper:
    def __init__(self):
        self.driver = None

    def init_driver(self):
        """Initialize headless Chrome driver"""
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={Config.USER_AGENT}')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape_brack(self, url):
        """Scrape Brack with Selenium"""
        self.init_driver()

        try:
            self.driver.get(url)

            # Wait for price to load (adjust selector as needed)
            wait = WebDriverWait(self.driver, 10)

            # Try multiple selectors
            price_selectors = [
                (By.CLASS_NAME, 'price'),
                (By.CSS_SELECTOR, '[data-test="productPrice"]'),
                (By.CSS_SELECTOR, '.product-price'),
            ]

            price_text = None
            for by, selector in price_selectors:
                try:
                    element = wait.until(EC.presence_of_element_located((by, selector)))
                    price_text = element.text
                    if price_text:
                        break
                except:
                    continue

            # Get product name
            name = None
            try:
                name_elem = self.driver.find_element(By.TAG_NAME, 'h1')
                name = name_elem.text
            except:
                pass

            # Extract price
            price = self._extract_price(price_text) if price_text else None

            return {
                'url': url,
                'name': name,
                'price': price,
                'currency': 'CHF',
                'image_url': None
            }

        except Exception as e:
            print(f"Selenium error for {url}: {str(e)}")
            return None

    def scrape_digitec(self, url):
        """Scrape Digitec with Selenium"""
        self.init_driver()

        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)

            # Wait for price
            price_selectors = [
                (By.CSS_SELECTOR, '[data-test="productPrice"]'),
                (By.CLASS_NAME, 'price'),
                (By.CSS_SELECTOR, '.product-price'),
            ]

            price_text = None
            for by, selector in price_selectors:
                try:
                    element = wait.until(EC.presence_of_element_located((by, selector)))
                    price_text = element.text
                    if price_text:
                        break
                except:
                    continue

            # Get product name
            name = None
            try:
                name_elem = self.driver.find_element(By.TAG_NAME, 'h1')
                name = name_elem.text
            except:
                pass

            price = self._extract_price(price_text) if price_text else None

            return {
                'url': url,
                'name': name,
                'price': price,
                'currency': 'CHF',
                'image_url': None
            }

        except Exception as e:
            print(f"Selenium error for {url}: {str(e)}")
            return None

    def _extract_price(self, price_text):
        """Extract price from text"""
        if not price_text:
            return None

        # Remove currency and whitespace
        price_text = re.sub(r'[€$£CHF]|EUR|USD|GBP|Fr\.', '', price_text).strip()
        # Remove apostrophes (Swiss format)
        price_text = price_text.replace("'", '')
        # Handle comma as decimal separator
        if re.search(r',\d{2}$', price_text):
            price_text = price_text.replace('.', '').replace(',', '.')
        else:
            price_text = price_text.replace(',', '')

        try:
            return float(price_text)
        except:
            return None


# Usage example:
if __name__ == '__main__':
    scraper = SeleniumScraper()

    try:
        # Test Brack
        result = scraper.scrape_brack('https://www.brack.ch/seagate-harddisk-exos-x20-3-5-sas-20-tb-1299942')
        print(f"Brack: {result}")

        # Test Digitec
        result = scraper.scrape_digitec('https://www.digitec.ch/de/s1/product/seagate-exos-x20-18-tb-35-festplatte-17828191')
        print(f"Digitec: {result}")

    finally:
        scraper.close()
