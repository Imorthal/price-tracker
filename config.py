import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'price_tracker.db')

    # Scraper
    SCRAPE_INTERVAL_MINUTES = int(os.getenv('SCRAPE_INTERVAL_MINUTES', '60'))
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    REQUEST_TIMEOUT = 10

    # Price alert threshold (percentage)
    PRICE_DROP_THRESHOLD = float(os.getenv('PRICE_DROP_THRESHOLD', '5.0'))
