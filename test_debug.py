#!/usr/bin/env python
"""Debug script to test scraping with detailed output"""

from scraper import PriceScraper

scraper = PriceScraper()

# Test URLs
urls = {
    'Brack': 'https://www.brack.ch/seagate-harddisk-exos-x20-3-5-sas-20-tb-1299942',
    'Digitec': 'https://www.digitec.ch/de/s1/product/seagate-exos-x20-18-tb-35-festplatte-17828191',
}

for shop, url in urls.items():
    print(f"\n{'='*80}")
    print(f"Testing {shop}")
    print('='*80)

    result = scraper.scrape_product(url, debug=True)

    if result:
        print(f"\n✓ Result:")
        print(f"  Name: {result.get('name', 'N/A')}")
        print(f"  Price: {result.get('price', 'N/A')} {result.get('currency', 'N/A')}")
        print(f"  Image: {'Yes' if result.get('image_url') else 'No'}")
    else:
        print(f"\n✗ Failed to scrape!")
