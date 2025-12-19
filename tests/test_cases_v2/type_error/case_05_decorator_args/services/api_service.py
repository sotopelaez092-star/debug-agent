"""API service with cached external calls."""
from decorators import cache
import time


class APIService:
    """Service for external API calls with caching."""

    def __init__(self, api_base_url="https://api.example.com"):
        self.api_base_url = api_base_url
        self.request_count = 0

    @cache  # BUG: Old syntax without TTL
    def fetch_weather_data(self, city):
        """
        Fetch weather data from external API (expensive operation).

        Uses old @cache decorator syntax.
        """
        self.request_count += 1
        print(f"  [API] Fetching weather for {city}...")
        time.sleep(0.15)

        # Simulated API response
        return {
            "city": city,
            "temperature": 20 + (hash(city) % 15),
            "humidity": 50 + (hash(city) % 30),
            "condition": "Sunny",
            "timestamp": time.time(),
        }

    @cache  # BUG: Old syntax
    def get_exchange_rate(self, from_currency, to_currency):
        """Get currency exchange rate (cached)."""
        self.request_count += 1
        print(f"  [API] Fetching exchange rate {from_currency} -> {to_currency}...")
        time.sleep(0.15)

        # Simulated rates
        rates = {
            "USD_EUR": 0.85,
            "USD_GBP": 0.73,
            "EUR_USD": 1.18,
            "GBP_USD": 1.37,
        }

        rate_key = f"{from_currency}_{to_currency}"
        return {
            "from": from_currency,
            "to": to_currency,
            "rate": rates.get(rate_key, 1.0),
            "timestamp": time.time(),
        }

    def get_request_count(self):
        """Get number of actual API requests made."""
        return self.request_count

    def reset_count(self):
        """Reset request counter."""
        self.request_count = 0
