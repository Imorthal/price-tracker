import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from config import Config

class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def scrape_product(self, url):
        """
        Scrape product information from URL.
        Returns dict with name, price, currency, and image_url.
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            domain = urlparse(url).netloc.lower()

            # Try to detect the shop and use specific selectors
            if 'amazon' in domain:
                return self._scrape_amazon(soup, url)
            elif 'ebay' in domain:
                return self._scrape_ebay(soup, url)
            else:
                # Generic scraping
                return self._scrape_generic(soup, url)

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def _scrape_amazon(self, soup, url):
        """Scrape Amazon product page"""
        product = {
            'url': url,
            'name': None,
            'price': None,
            'currency': 'EUR',
            'image_url': None
        }

        # Product name
        title_elem = soup.find('span', {'id': 'productTitle'})
        if title_elem:
            product['name'] = title_elem.get_text().strip()

        # Price - Amazon has multiple possible price locations
        price_selectors = [
            ('span', {'class': 'a-price-whole'}),
            ('span', {'class': 'a-offscreen'}),
            ('span', {'id': 'priceblock_ourprice'}),
            ('span', {'id': 'priceblock_dealprice'}),
        ]

        for tag, attrs in price_selectors:
            price_elem = soup.find(tag, attrs)
            if price_elem:
                price_text = price_elem.get_text()
                price = self._extract_price(price_text)
                if price:
                    product['price'] = price
                    break

        # Image
        img_elem = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'class': 'a-dynamic-image'})
        if img_elem and img_elem.get('src'):
            product['image_url'] = img_elem['src']

        return product

    def _scrape_ebay(self, soup, url):
        """Scrape eBay product page"""
        product = {
            'url': url,
            'name': None,
            'price': None,
            'currency': 'EUR',
            'image_url': None
        }

        # Product name
        title_elem = soup.find('h1', {'class': 'x-item-title__mainTitle'})
        if title_elem:
            product['name'] = title_elem.get_text().strip()

        # Price
        price_elem = soup.find('div', {'class': 'x-price-primary'}) or \
                     soup.find('span', {'itemprop': 'price'})
        if price_elem:
            price_text = price_elem.get_text()
            price = self._extract_price(price_text)
            if price:
                product['price'] = price

        # Image
        img_elem = soup.find('img', {'id': 'icImg'}) or soup.find('img', {'class': 'vi-image-gallery__image'})
        if img_elem and img_elem.get('src'):
            product['image_url'] = img_elem['src']

        return product

    def _scrape_generic(self, soup, url):
        """Generic scraping for unknown shops"""
        product = {
            'url': url,
            'name': None,
            'price': None,
            'currency': 'EUR',
            'image_url': None
        }

        # Try to find product name
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            product['name'] = title_elem.get_text().strip()[:200]

        # Try to find price using common patterns
        price_patterns = [
            r'(\d+[.,]\d{2})\s*€',
            r'€\s*(\d+[.,]\d{2})',
            r'EUR\s*(\d+[.,]\d{2})',
            r'(\d+[.,]\d{2})\s*EUR',
        ]

        page_text = soup.get_text()
        for pattern in price_patterns:
            match = re.search(pattern, page_text)
            if match:
                price_text = match.group(1)
                price = self._extract_price(price_text)
                if price and 0.01 <= price <= 1000000:  # Sanity check
                    product['price'] = price
                    break

        # Try to find image
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image and og_image.get('content'):
            product['image_url'] = og_image['content']
        else:
            img_elem = soup.find('img')
            if img_elem and img_elem.get('src'):
                product['image_url'] = img_elem['src']

        return product

    def _extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None

        # Remove currency symbols and text
        price_text = re.sub(r'[^\d.,]', '', price_text)

        # Replace comma with dot for decimal
        price_text = price_text.replace(',', '.')

        # Remove all dots except the last one (for thousands separator)
        parts = price_text.split('.')
        if len(parts) > 2:
            price_text = ''.join(parts[:-1]) + '.' + parts[-1]

        try:
            return float(price_text)
        except (ValueError, AttributeError):
            return None
