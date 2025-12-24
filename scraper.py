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

    def scrape_product(self, url, debug=False):
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

            if debug:
                print(f"\n=== DEBUG: Scraping {url} ===")
                print(f"Domain: {domain}")
                print(f"Response status: {response.status_code}")
                print(f"Content length: {len(response.content)} bytes")

            # Try to detect the shop and use specific selectors
            if 'amazon' in domain:
                result = self._scrape_amazon(soup, url)
            elif 'ebay' in domain:
                result = self._scrape_ebay(soup, url)
            elif 'brack.ch' in domain:
                result = self._scrape_brack(soup, url)
            elif 'digitec.ch' in domain:
                result = self._scrape_digitec(soup, url)
            else:
                # Generic scraping
                result = self._scrape_generic(soup, url)

            if debug:
                print(f"Scraped result: {result}")
                if not result or not result.get('price'):
                    print("WARNING: No price found!")
                    # Print first 500 chars of page text for debugging
                    page_text = soup.get_text()[:500]
                    print(f"Page text sample: {page_text}")

            return result

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            import traceback
            traceback.print_exc()
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

    def _scrape_brack(self, soup, url):
        """Scrape Brack.ch product page"""
        product = {
            'url': url,
            'name': None,
            'price': None,
            'currency': 'CHF',
            'image_url': None
        }

        # Product name - multiple selectors
        title_selectors = [
            ('h1', {'class': 'product-name'}),
            ('h1', {'class': 'product__name'}),
            ('h1', {'class': 'product-title'}),
            ('h1', {'data-test': 'productName'}),
            ('h1', {}),
            ('meta', {'property': 'og:title'})
        ]

        for tag, attrs in title_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                if tag == 'meta':
                    product['name'] = elem.get('content', '').strip()
                else:
                    product['name'] = elem.get_text().strip()
                if product['name']:
                    break

        # Price - multiple approaches for Brack
        # 1. Try common price selectors (most specific first)
        price_selectors = [
            # Specific Brack selectors
            ('span', {'data-test': 'productPrice'}),
            ('div', {'data-test': 'productPrice'}),
            ('span', {'class': 'productPrice'}),
            ('div', {'class': 'productPrice'}),
            # Generic price selectors
            ('span', {'class': 'price'}),
            ('div', {'class': 'price'}),
            ('span', {'class': 'product-price'}),
            ('div', {'class': 'product-price'}),
            ('span', {'class': 'product__price'}),
            ('div', {'class': 'product__price'}),
            ('div', {'class': 'price-box'}),
            ('span', {'itemprop': 'price'}),
            ('meta', {'itemprop': 'price'}),
            # Data attributes
            ('div', {'data-price': True}),
            ('span', {'data-price': True}),
        ]

        for tag, attrs in price_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                if tag == 'meta':
                    price_text = elem.get('content', '')
                elif 'data-price' in attrs:
                    # Try data attribute first
                    price_text = elem.get('data-price', '') or elem.get_text()
                else:
                    price_text = elem.get_text()

                if price_text:
                    price = self._extract_price(price_text)
                    if price and 0.01 <= price <= 1000000:
                        product['price'] = price
                        break

        # 2. Try meta tags
        if not product['price']:
            meta_selectors = [
                {'property': 'product:price:amount'},
                {'property': 'og:price:amount'},
                {'name': 'product:price:amount'}
            ]
            for selector in meta_selectors:
                price_meta = soup.find('meta', selector)
                if price_meta and price_meta.get('content'):
                    try:
                        product['price'] = float(price_meta['content'].replace(',', '.'))
                        break
                    except:
                        pass

        # 3. Try JSON-LD structured data
        if not product['price']:
            try:
                import json
                json_ld = soup.find('script', {'type': 'application/ld+json'})
                if json_ld:
                    data = json.loads(json_ld.string)
                    if isinstance(data, dict):
                        if 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, dict) and 'price' in offers:
                                product['price'] = float(offers['price'])
                            elif isinstance(offers, list) and len(offers) > 0:
                                product['price'] = float(offers[0].get('price', 0))
            except:
                pass

        # 4. Scan all elements for price-like content
        if not product['price']:
            # Find all elements with numbers that look like prices
            all_text_elements = soup.find_all(text=re.compile(r'\d+[\.,]\d{2}'))

            for text_elem in all_text_elements:
                text = text_elem.strip()
                # Skip if it's in a script or style tag
                if text_elem.parent.name in ['script', 'style']:
                    continue

                # Look for CHF prices
                if re.search(r'(?:CHF|Fr\.)', text, re.IGNORECASE):
                    price = self._extract_price(text)
                    if price and 10 <= price <= 100000:  # Reasonable price range
                        product['price'] = price
                        break

        # 5. Fallback: search for price patterns in page text
        if not product['price']:
            page_text = soup.get_text()
            # Swiss price patterns (CHF with apostrophe thousands separator)
            patterns = [
                r"(?:CHF|Fr\.)\s*([0-9]+'[0-9]{3}\.[0-9]{2})",
                r"(?:CHF|Fr\.)\s*([0-9]+'[0-9]{3},\d{2})",
                r"(?:CHF|Fr\.)\s*([0-9]+\.[0-9]{2})",
                r"(?:CHF|Fr\.)\s*([0-9]+,\d{2})",
                r"([0-9]+'[0-9]{3}\.[0-9]{2})\s*(?:CHF|Fr\.)",
                r"([0-9]+'[0-9]{3},\d{2})\s*(?:CHF|Fr\.)",
                r"([0-9]+\.[0-9]{2})\s*(?:CHF|Fr\.)",
                r"([0-9]+,\d{2})\s*(?:CHF|Fr\.)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    price = self._extract_price(match)
                    if price and 10 <= price <= 100000:  # Sanity check for reasonable price
                        product['price'] = price
                        break
                if product['price']:
                    break

        # Image
        img_elem = soup.find('img', {'class': 'product-image'}) or \
                   soup.find('img', {'data-test': 'productImage'}) or \
                   soup.find('meta', {'property': 'og:image'})

        if img_elem:
            if img_elem.name == 'meta':
                product['image_url'] = img_elem.get('content')
            else:
                product['image_url'] = img_elem.get('src') or img_elem.get('data-src')

        return product

    def _scrape_digitec(self, soup, url):
        """Scrape Digitec.ch product page"""
        product = {
            'url': url,
            'name': None,
            'price': None,
            'currency': 'CHF',
            'image_url': None
        }

        # Product name - multiple selectors
        title_selectors = [
            ('h1', {'class': 'productTitle'}),
            ('h1', {'data-test': 'productName'}),
            ('strong', {'data-test': 'productName'}),
            ('h1', {'class': 'product-title'}),
            ('h1', {}),
            ('meta', {'property': 'og:title'})
        ]

        for tag, attrs in title_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                if tag == 'meta':
                    product['name'] = elem.get('content', '').strip()
                else:
                    product['name'] = elem.get_text().strip()
                if product['name']:
                    break

        # Price - multiple approaches for Digitec/Galaxus
        # 1. Try common price selectors
        price_selectors = [
            ('strong', {'data-test': 'productPrice'}),
            ('span', {'data-test': 'productPrice'}),
            ('div', {'data-test': 'productPrice'}),
            ('span', {'class': 'price'}),
            ('div', {'class': 'product-price'}),
            ('span', {'class': 'product__price'}),
            ('span', {'itemprop': 'price'}),
        ]

        for tag, attrs in price_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                price_text = elem.get_text()
                price = self._extract_price(price_text)
                if price:
                    product['price'] = price
                    break

        # 2. Try meta tags
        if not product['price']:
            meta_selectors = [
                {'property': 'product:price:amount'},
                {'property': 'og:price:amount'},
                {'name': 'product:price:amount'}
            ]
            for selector in meta_selectors:
                price_meta = soup.find('meta', selector)
                if price_meta and price_meta.get('content'):
                    try:
                        product['price'] = float(price_meta['content'].replace(',', '.'))
                        break
                    except:
                        pass

        # 3. Try JSON-LD structured data
        if not product['price']:
            try:
                import json
                scripts = soup.find_all('script', {'type': 'application/ld+json'})
                for json_ld in scripts:
                    try:
                        data = json.loads(json_ld.string)
                        # Handle both single object and array
                        items = [data] if isinstance(data, dict) else data
                        for item in items:
                            if isinstance(item, dict) and 'offers' in item:
                                offers = item['offers']
                                if isinstance(offers, dict) and 'price' in offers:
                                    product['price'] = float(offers['price'])
                                    break
                                elif isinstance(offers, list) and len(offers) > 0:
                                    product['price'] = float(offers[0].get('price', 0))
                                    break
                        if product['price']:
                            break
                    except:
                        continue
            except:
                pass

        # 4. Fallback: search for price patterns in page text
        if not product['price']:
            page_text = soup.get_text()
            # Swiss price patterns
            patterns = [
                r"(?:CHF|Fr\.)\s*([0-9]+'[0-9]{3}\.[0-9]{2})",
                r"(?:CHF|Fr\.)\s*([0-9]+\.[0-9]{2})",
                r"([0-9]+'[0-9]{3}\.[0-9]{2})\s*(?:CHF|Fr\.)",
                r"([0-9]+\.[0-9]{2})\s*(?:CHF|Fr\.)"
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    price = self._extract_price(match.group(1))
                    if price and 1 <= price <= 100000:  # Sanity check
                        product['price'] = price
                        break

        # Image
        img_elem = soup.find('img', {'data-test': 'productImage'}) or \
                   soup.find('picture', {'class': 'product-image'}) or \
                   soup.find('meta', {'property': 'og:image'})

        if img_elem:
            if img_elem.name == 'meta':
                product['image_url'] = img_elem.get('content')
            elif img_elem.name == 'picture':
                img_tag = img_elem.find('img')
                if img_tag:
                    product['image_url'] = img_tag.get('src') or img_tag.get('data-src')
            else:
                product['image_url'] = img_elem.get('src') or img_elem.get('data-src')

        return product

    def _extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None

        # Remove currency symbols (€, CHF, EUR, etc.) and whitespace
        price_text = re.sub(r'[€$£CHF]|EUR|USD|GBP', '', price_text).strip()

        # Remove all non-numeric characters except dots, commas, and apostrophes (Swiss format)
        price_text = re.sub(r"[^\d.,']", '', price_text)

        # Handle Swiss format (e.g., 1'234.56 or 1'234,56)
        price_text = price_text.replace("'", '')

        # Determine decimal separator
        # If there's a comma followed by 2 digits at the end, it's decimal
        # Otherwise, comma is thousands separator
        if re.search(r',\d{2}$', price_text):
            # Comma is decimal separator (European format)
            price_text = price_text.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal separator or comma is thousands
            price_text = price_text.replace(',', '')

        try:
            return float(price_text)
        except (ValueError, AttributeError):
            return None
