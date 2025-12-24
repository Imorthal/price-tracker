#!/usr/bin/env python
"""Test script to verify scraping functionality"""

from scraper import PriceScraper
import json

# Initialize scraper
scraper = PriceScraper()

# Test URLs
urls = {
    'Brack': 'https://www.brack.ch/seagate-harddisk-exos-x20-3-5-sas-20-tb-1299942',
    'Digitec': 'https://www.digitec.ch/de/s1/product/seagate-exos-x20-18-tb-35-festplatte-17828191',
    'Amazon': 'https://www.amazon.de/Seagate-Enterprise-Festplatte-Hyperscale-Modellnr/dp/B09MWLJ1P5'
}

print("Testing Price Scraper\n" + "="*80)

for shop, url in urls.items():
    print(f"\n{shop}:")
    print(f"URL: {url}")
    print("-" * 80)

    try:
        result = scraper.scrape_product(url)

        if result:
            print(f"✓ Success!")
            print(f"  Name: {result.get('name', 'N/A')}")
            print(f"  Price: {result.get('price', 'N/A')} {result.get('currency', 'N/A')}")
            print(f"  Image: {'Yes' if result.get('image_url') else 'No'}")
        else:
            print("✗ Failed to scrape product data")

    except Exception as e:
        print(f"✗ Error: {str(e)}")

print("\n" + "="*80)
