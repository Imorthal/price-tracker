# Price Tracker

Ein moderner Web-basierter Price Tracker zum Überwachen von Produktpreisen aus verschiedenen Online-Shops.

## Features

- **Automatisches Preis-Scraping**: Unterstützt Amazon, eBay, Brack, Digitec und viele weitere Shops
- **Multi-Shop-Vergleich**: Verfolge dasselbe Produkt bei mehreren Anbietern gleichzeitig
- **Preisverlauf**: Visualisierung der Preisentwicklung über die Zeit pro Shop
- **Automatische Updates**: Konfigurierbare automatische Preisüberprüfung für alle Quellen
- **Responsives Design**: Funktioniert auf Desktop und Mobile
- **Einfache Bedienung**: Intuitive Web-Oberfläche
- **Statistiken**: Übersicht über potentielle Ersparnisse und Durchschnittspreise
- **Flexible Produktgruppierung**: Füge manuell weitere Shops zu einem Produkt hinzu

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)

### Setup

1. Repository klonen:
```bash
git clone <repository-url>
cd price-tracker
```

2. Virtuelle Umgebung erstellen (empfohlen):
```bash
python -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate
```

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

4. Umgebungsvariablen konfigurieren (optional):
```bash
cp .env.example .env
# Bearbeite .env nach Bedarf
```

## Verwendung

### Server starten

```bash
python app.py
```

Der Server läuft standardmäßig auf `http://localhost:5000`

### Web-Interface nutzen

1. Öffne `http://localhost:5000` im Browser
2. Gib eine Produkt-URL ein (z.B. von Amazon, eBay, Brack oder Digitec)
3. Klicke auf "Produkt hinzufügen"
4. Der Tracker wird automatisch den aktuellen Preis abrufen und speichern

### Multi-Shop-Vergleich

Um dasselbe Produkt bei verschiedenen Shops zu vergleichen:

1. Füge zunächst eine URL des Produkts hinzu (z.B. von Amazon)
2. Klicke auf "+ Shop" bei dem Produkt
3. Gib die URL desselben Produkts von einem anderen Shop ein (z.B. Brack oder Digitec)
4. Das System zeigt nun beide Preise nebeneinander an und verfolgt sie separat

**Tipp**: Die App erkennt automatisch den Shop (Amazon, Brack, Digitec, etc.) und nutzt optimierte Scraper.

### Automatische Updates

Der Tracker überprüft standardmäßig alle 60 Minuten automatisch alle Produkte.
Dies kann in der `.env` Datei oder `config.py` angepasst werden.

## Konfiguration

### Umgebungsvariablen

Erstelle eine `.env` Datei mit folgenden Optionen:

```env
# Flask Konfiguration
SECRET_KEY=dein-geheimer-schluessel
DEBUG=True

# Datenbank
DATABASE_PATH=price_tracker.db

# Scraper Einstellungen
SCRAPE_INTERVAL_MINUTES=60
PRICE_DROP_THRESHOLD=5.0
```

### Wichtige Parameter

- `SCRAPE_INTERVAL_MINUTES`: Intervall für automatische Preisupdates (in Minuten)
- `PRICE_DROP_THRESHOLD`: Schwellenwert für Preisänderungen in Prozent
- `DATABASE_PATH`: Pfad zur SQLite Datenbank

## API Endpunkte

### GET /api/products
Alle getrackte Produkte abrufen (inkl. aller Sources)

### POST /api/products
Neues Produkt hinzufügen
```json
{
  "url": "https://www.amazon.de/..."
}
```

### DELETE /api/products/{id}
Produkt löschen

### POST /api/products/{id}/refresh
Produkt manuell aktualisieren

### GET /api/products/{id}/history
Preisverlauf für ein Produkt abrufen

### GET /api/products/{id}/sources
Alle Sources (Shop-URLs) für ein Produkt abrufen

### POST /api/products/{id}/sources
Neue Source zu einem Produkt hinzufügen
```json
{
  "url": "https://www.brack.ch/..."
}
```

### DELETE /api/sources/{id}
Eine Source löschen

### POST /api/update-all
Alle Produkte und Sources manuell aktualisieren

## Projektstruktur

```
price-tracker/
├── app.py              # Flask Hauptanwendung
├── config.py           # Konfiguration
├── database.py         # Datenbank-Logik
├── scraper.py          # Web-Scraping Logik
├── requirements.txt    # Python Abhängigkeiten
├── static/
│   ├── index.html     # Frontend HTML
│   ├── style.css      # Styling
│   └── script.js      # Frontend JavaScript
└── README.md          # Diese Datei
```

## Unterstützte Shops

### Mit optimierten Scrapern:
- **Amazon** (alle Länder) - .de, .com, .co.uk, etc.
- **eBay** (alle Länder)
- **Brack.ch** (Schweiz) - Optimiert für Brack
- **Digitec.ch** (Schweiz) - Optimiert für Digitec/Galaxus

### Generisches Scraping:
- Die meisten anderen Online-Shops werden durch generisches Scraping unterstützt
- Erfolgsrate kann variieren je nach Website-Struktur

**Hinweis**: Einige Shops haben Anti-Scraping-Maßnahmen. Die Erfolgsrate kann variieren. Bei Problemen nutze einen längeren Scraping-Intervall.

## Technologie-Stack

- **Backend**: Python, Flask
- **Database**: SQLite
- **Scraping**: BeautifulSoup4, Requests
- **Scheduling**: APScheduler
- **Frontend**: Vanilla JavaScript, CSS3, HTML5

## Entwicklung

### Lokales Testing

```bash
# Entwicklungsserver mit Auto-Reload
python app.py
```

### Neue Shop-Unterstützung hinzufügen

Füge eine neue Methode in `scraper.py` hinzu:

```python
def _scrape_shopname(self, soup, url):
    # Implementiere Shop-spezifische Scraping-Logik
    pass
```

## Bekannte Einschränkungen

- Einige Shops blockieren möglicherweise automatisierte Anfragen
- JavaScript-basierte Preise können nicht abgerufen werden
- Rate-Limiting kann zu Verzögerungen führen

## Rechtliche Hinweise

Dieses Tool ist nur für den persönlichen, nicht-kommerziellen Gebrauch bestimmt.
Bitte beachte die Nutzungsbedingungen der jeweiligen Websites.
Exzessives Scraping kann zu IP-Sperren führen.

## Lizenz

MIT License - Siehe LICENSE Datei für Details

## Support

Bei Problemen oder Fragen bitte ein Issue im GitHub Repository erstellen.

## Roadmap

- [x] Multi-Shop-Vergleich (Mehrere URLs pro Produkt)
- [x] Unterstützung für Brack.ch und Digitec.ch
- [x] Verbesserte Preisextraktion (Schweizer Format mit ')
- [ ] E-Mail Benachrichtigungen bei Preisänderungen
- [ ] Preis-Alerts mit individuellen Schwellenwerten pro Shop
- [ ] Export von Preisverläufen (CSV, JSON)
- [ ] Automatische Produkterkennung (gleiche Produkte automatisch verknüpfen)
- [ ] Unterstützung für weitere Shops (MediaMarkt, Otto, etc.)
- [ ] Mobile App
- [ ] Multi-User Support mit Authentifizierung
- [ ] Preisvergleichs-Dashboard mit Best-Price-Anzeige
