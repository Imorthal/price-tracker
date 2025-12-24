"""
Currency conversion service using exchangerate-api.com
Free tier: 1,500 requests/month
"""

import requests
from datetime import datetime, timedelta
from database import Database

class CurrencyConverter:
    def __init__(self):
        self.db = Database()
        self.base_currency = 'CHF'
        self.api_url = 'https://api.exchangerate-api.com/v4/latest/{}'
        self.cache_duration = timedelta(hours=6)  # Update rates every 6 hours
        self.last_update = None

    def get_exchange_rates(self):
        """Get current exchange rates to CHF"""
        # Check cache first
        cached_rates = self._get_cached_rates()
        if cached_rates:
            self.last_update = cached_rates['timestamp']
            return cached_rates

        # Fetch new rates
        try:
            # Get rates with CHF as base
            response = requests.get(self.api_url.format(self.base_currency), timeout=5)
            response.raise_for_status()
            data = response.json()

            rates = {
                'EUR': 1 / data['rates']['EUR'] if 'EUR' in data['rates'] else 0,
                'USD': 1 / data['rates']['USD'] if 'USD' in data['rates'] else 0,
                'GBP': 1 / data['rates']['GBP'] if 'GBP' in data['rates'] else 0,
                'CHF': 1.0,
                'timestamp': datetime.now().isoformat()
            }

            # Cache the rates
            self._cache_rates(rates)
            self.last_update = rates['timestamp']

            return rates

        except Exception as e:
            print(f"Error fetching exchange rates: {str(e)}")
            # Return fallback rates
            fallback = {
                'EUR': 0.93,  # Approximate fallback
                'USD': 0.84,
                'GBP': 1.08,
                'CHF': 1.0,
                'timestamp': datetime.now().isoformat()
            }
            self.last_update = fallback['timestamp']
            return fallback

    def _get_cached_rates(self):
        """Get rates from cache if still valid"""
        try:
            timestamp_str = self.db.get_setting('exchange_rates_timestamp')
            if not timestamp_str:
                return None

            timestamp = datetime.fromisoformat(timestamp_str)
            if datetime.now() - timestamp > self.cache_duration:
                return None

            # Get cached rates
            rates = {
                'EUR': float(self.db.get_setting('exchange_rate_eur', '0.93')),
                'USD': float(self.db.get_setting('exchange_rate_usd', '0.84')),
                'GBP': float(self.db.get_setting('exchange_rate_gbp', '1.08')),
                'CHF': 1.0,
                'timestamp': timestamp_str
            }

            return rates

        except Exception as e:
            print(f"Error reading cached rates: {str(e)}")
            return None

    def _cache_rates(self, rates):
        """Cache exchange rates"""
        try:
            self.db.update_setting('exchange_rates_timestamp', rates['timestamp'])
            self.db.update_setting('exchange_rate_eur', str(rates['EUR']))
            self.db.update_setting('exchange_rate_usd', str(rates['USD']))
            self.db.update_setting('exchange_rate_gbp', str(rates['GBP']))
        except Exception as e:
            print(f"Error caching rates: {str(e)}")

    def convert_to_chf(self, amount, from_currency):
        """Convert amount to CHF"""
        if not amount or from_currency == 'CHF':
            return amount

        rates = self.get_exchange_rates()

        # Get conversion rate
        from_currency = from_currency.upper()
        if from_currency not in rates:
            print(f"Warning: Unknown currency {from_currency}, using as CHF")
            return amount

        # Convert to CHF
        chf_amount = amount * rates[from_currency]
        return round(chf_amount, 2)

    def get_rate_for_display(self, currency):
        """Get exchange rate for display (1 CURRENCY = X CHF)"""
        if currency == 'CHF':
            return 1.0

        rates = self.get_exchange_rates()
        return rates.get(currency.upper(), 1.0)
