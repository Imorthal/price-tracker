# Price Tracker

Ein moderner Web-basierter Price Tracker zum Überwachen von Produktpreisen aus verschiedenen Online-Shops.

## Features

- **Automatisches Preis-Scraping**: Unterstützt Amazon, eBay und viele weitere Shops
- **Preisverlauf**: Visualisierung der Preisentwicklung über die Zeit
- **Automatische Updates**: Konfigurierbare automatische Preisüberprüfung
- **Responsives Design**: Funktioniert auf Desktop und Mobile
- **Einfache Bedienung**: Intuitive Web-Oberfläche
- **Statistiken**: Übersicht über potentielle Ersparnisse und Durchschnittspreise

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
2. Gib eine Produkt-URL ein (z.B. von Amazon oder eBay)
3. Klicke auf "Produkt hinzufügen"
4. Der Tracker wird automatisch den aktuellen Preis abrufen und speichern

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
Alle getrackte Produkte abrufen

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

### POST /api/update-all
Alle Produkte manuell aktualisieren

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

- Amazon (alle Länder)
- eBay (alle Länder)
- Generisches Scraping für andere Shops

**Hinweis**: Einige Shops haben Anti-Scraping-Maßnahmen. Die Erfolgsrate kann variieren.

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

- [ ] E-Mail Benachrichtigungen bei Preisänderungen
- [ ] Preis-Alerts mit individuellen Schwellenwerten
- [ ] Export von Preisverläufen (CSV, JSON)
- [ ] Unterstützung für weitere Shops
- [ ] Mobile App
- [ ] Multi-User Support mit Authentifizierung
