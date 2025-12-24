# Troubleshooting Guide

## Problem: Brack oder Digitec zeigen "N/A" als Preis

### Ursache
Brack.ch und Digitec.ch sind moderne Single-Page-Applications, die ihre Inhalte dynamisch mit JavaScript laden. Der Standard-Scraper (BeautifulSoup) kann nur statisches HTML lesen.

### Lösung 1: Verbesserte Scraper testen (bereits implementiert)

Die Scraper verwenden jetzt mehrere Strategien:
1. Multiple HTML-Selektoren
2. JSON-LD structured data
3. Meta-Tags (OpenGraph)
4. Regex-basierte Preissuche

**Test durchführen:**
```bash
python test_debug.py
```

### Lösung 2: Selenium verwenden (für JavaScript-Seiten)

Falls die Standard-Scraper nicht funktionieren:

**1. Selenium installieren:**
```bash
pip install selenium webdriver-manager
```

**2. Selenium-Scraper testen:**
```bash
python scraper_selenium.py
```

**3. In die App integrieren:**

Öffne `scraper.py` und füge am Anfang hinzu:

```python
# Am Anfang der Datei
try:
    from scraper_selenium import SeleniumScraper
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    SeleniumScraper = None
```

In der `PriceScraper` Klasse:

```python
def __init__(self):
    self.headers = {...}
    self.selenium_scraper = SeleniumScraper() if SELENIUM_AVAILABLE else None

def scrape_product(self, url, debug=False):
    domain = urlparse(url).netloc.lower()

    # Use Selenium for Brack and Digitec if available
    if SELENIUM_AVAILABLE and self.selenium_scraper:
        if 'brack.ch' in domain:
            return self.selenium_scraper.scrape_brack(url)
        elif 'digitec.ch' in domain:
            return self.selenium_scraper.scrape_digitec(url)

    # ... rest of existing code
```

### Lösung 3: API nutzen (falls verfügbar)

Manche Shops haben APIs. Prüfe ob Brack/Digitec eine öffentliche API haben.

### Lösung 4: Manuelle Preise hinzufügen

Als Workaround kannst du die Preise manuell in der Datenbank aktualisieren.

## Problem: Scraping wird blockiert

### Symptome
- HTTP 403 Fehler
- Captchas
- Leere Responses

### Lösungen

**1. User-Agent anpassen** (in `config.py`):
```python
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

**2. Längere Intervalle** (in `.env`):
```env
SCRAPE_INTERVAL_MINUTES=120
```

**3. Delays zwischen Requests** (in `scraper.py`):
```python
import time

def scrape_product(self, url):
    time.sleep(2)  # 2 Sekunden warten
    # ... rest of code
```

**4. Proxies verwenden:**
```python
proxies = {
    'http': 'http://your-proxy:port',
    'https': 'http://your-proxy:port',
}
response = requests.get(url, headers=self.headers, proxies=proxies)
```

## Problem: Preise werden falsch extrahiert

### Symptome
- Preis ist 0 oder sehr hoch/niedrig
- Falsche Währung

### Debug-Schritte

**1. Debug-Modus aktivieren:**
```python
# In test_debug.py
result = scraper.scrape_product(url, debug=True)
```

**2. HTML inspizieren:**
```python
from scraper import PriceScraper
import requests
from bs4 import BeautifulSoup

url = "deine-url-hier"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'lxml')

# Speichere HTML
with open('debug.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

# Zeige alle möglichen Preis-Elemente
print(soup.find_all(text=re.compile(r'\d+\.\d{2}')))
```

**3. Selektoren anpassen:**

Öffne `scraper.py` und füge weitere Selektoren hinzu in den `price_selectors` Listen.

## Problem: Datenbank-Fehler

### Symptome
- "Database locked"
- Tabellen fehlen

### Lösungen

**1. Datenbank neu initialisieren:**
```bash
rm price_tracker.db
python -c "from database import Database; Database()"
```

**2. Migrationen durchführen:**

Falls du die Datenbank schon mit altem Schema hattest:
```bash
python migrate_db.py
```

## Support

Bei weiteren Problemen:
1. Prüfe die Logs im Terminal
2. Teste mit `test_debug.py`
3. Erstelle ein Issue im GitHub Repository mit:
   - URL die nicht funktioniert
   - Fehlermeldung
   - Debug-Output
