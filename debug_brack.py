#!/usr/bin/env python
"""
Specific debug script for Brack.ch
This will help us understand the HTML structure
"""

import requests
from bs4 import BeautifulSoup
from scraper import PriceScraper
import re

url = 'https://www.brack.ch/seagate-harddisk-exos-x20-3-5-sas-20-tb-1299942'

print("="*80)
print("DEBUGGING BRACK.CH")
print("="*80)

# Fetch the page
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.content, 'lxml')

    print(f"\nStatus Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes\n")

    # 1. Check for title
    print("1. PRODUCT NAME:")
    print("-" * 40)
    h1_tags = soup.find_all('h1')
    for i, h1 in enumerate(h1_tags):
        print(f"  H1 #{i}: {h1.get_text().strip()[:100]}")
        print(f"         Classes: {h1.get('class')}")

    og_title = soup.find('meta', {'property': 'og:title'})
    if og_title:
        print(f"  OG Title: {og_title.get('content')}")

    # 2. Check for price patterns in text
    print("\n2. PRICE PATTERNS IN PAGE TEXT:")
    print("-" * 40)
    page_text = soup.get_text()

    # Swiss price patterns
    patterns = [
        (r"(?:CHF|Fr\.)\s*([0-9]+'[0-9]{3}\.[0-9]{2})", "CHF X'XXX.XX"),
        (r"(?:CHF|Fr\.)\s*([0-9]+\.[0-9]{2})", "CHF XXX.XX"),
        (r"([0-9]+'[0-9]{3}\.[0-9]{2})\s*(?:CHF|Fr\.)", "X'XXX.XX CHF"),
        (r"([0-9]+\.[0-9]{2})\s*(?:CHF|Fr\.)", "XXX.XX CHF"),
    ]

    for pattern, desc in patterns:
        matches = re.findall(pattern, page_text)
        if matches:
            print(f"  {desc}: {matches[:5]}")  # Show first 5 matches

    # 3. Check for JSON-LD
    print("\n3. JSON-LD DATA:")
    print("-" * 40)
    json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    print(f"  Found {len(json_ld_scripts)} JSON-LD script(s)")

    for i, script in enumerate(json_ld_scripts[:2]):  # Show first 2
        try:
            import json
            data = json.loads(script.string)
            print(f"\n  Script #{i}:")
            print(f"    Type: {data.get('@type', 'unknown')}")
            if 'offers' in data:
                print(f"    Has offers: Yes")
                offers = data['offers']
                if isinstance(offers, dict):
                    print(f"      Price: {offers.get('price', 'N/A')}")
                    print(f"      Currency: {offers.get('priceCurrency', 'N/A')}")
        except Exception as e:
            print(f"  Script #{i}: Error parsing - {str(e)}")

    # 4. Check for price meta tags
    print("\n4. PRICE META TAGS:")
    print("-" * 40)
    meta_tags = [
        'product:price:amount',
        'og:price:amount',
        'twitter:data1',
    ]

    for tag in meta_tags:
        meta = soup.find('meta', {'property': tag}) or soup.find('meta', {'name': tag})
        if meta:
            print(f"  {tag}: {meta.get('content')}")

    # 5. Check for price elements
    print("\n5. COMMON PRICE ELEMENTS:")
    print("-" * 40)

    price_selectors = [
        ('span', {'class': 'price'}),
        ('div', {'class': 'price'}),
        ('span', {'class': 'product-price'}),
        ('div', {'class': 'product-price'}),
        ('span', {'itemprop': 'price'}),
        ('div', {'data-price': True}),
    ]

    for tag, attrs in price_selectors:
        elems = soup.find_all(tag, attrs)
        if elems:
            for elem in elems[:3]:  # Show first 3
                text = elem.get_text().strip()[:50]
                print(f"  <{tag} {attrs}>: {text}")

    # 6. Search for elements containing numbers
    print("\n6. ELEMENTS WITH PRICE-LIKE TEXT:")
    print("-" * 40)

    # Find all elements with price-like content
    all_elems = soup.find_all(text=re.compile(r'\d+\.\d{2}'))
    price_candidates = []

    for elem in all_elems:
        text = elem.strip()
        if re.search(r'\d+\.\d{2}', text):
            parent = elem.parent
            if parent and parent.name:
                price_candidates.append((parent.name, parent.get('class', []), text[:50]))

    # Show unique candidates
    unique_candidates = []
    seen = set()
    for name, classes, text in price_candidates:
        key = (name, str(classes), text)
        if key not in seen and len(unique_candidates) < 10:
            seen.add(key)
            unique_candidates.append((name, classes, text))

    for name, classes, text in unique_candidates:
        print(f"  <{name} class='{classes}'>: {text}")

    # 7. Try the actual scraper
    print("\n7. ACTUAL SCRAPER RESULT:")
    print("-" * 40)
    scraper = PriceScraper()
    result = scraper.scrape_product(url, debug=False)

    if result:
        print(f"  Name: {result.get('name', 'N/A')}")
        print(f"  Price: {result.get('price', 'N/A')}")
        print(f"  Currency: {result.get('currency', 'N/A')}")
    else:
        print("  ✗ Scraper returned None")

    # 8. Save HTML for manual inspection
    print("\n8. SAVING HTML:")
    print("-" * 40)
    with open('/home/user/price-tracker/debug_brack.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print("  Saved to: debug_brack.html")

except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
