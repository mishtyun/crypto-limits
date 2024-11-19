import time

import requests
import logging

class CoinGeckoAPI:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def _make_request(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Make a GET request to the CoinGecko API.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            time.sleep(1)
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {}

    def get_price(self, coin_id: str, vs_currencies: str = "usd") -> dict:
        """
        Get the current price of a coin.
        """
        endpoint = "simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currencies
        }
        return self._make_request(endpoint, params)

    def get_coin_list(self) -> list[dict]:
        """
        Get the list of all supported coins.
        """
        endpoint = "coins/list"
        return self._make_request(endpoint)

    def search_coins(self, query: str) -> dict:
        """
        Search for coins, categories and markets listed on CoinGecko.
        """
        endpoint = "search"
        params = {"query": query}
        return self._make_request(endpoint, params)

    def get_coin_history(self, coin_id: str, date: str) -> dict:
        """
        Get historical data (name, price, market, stats) at a given date for a coin.
        """
        endpoint = f"coins/{coin_id}/history"
        params = {"date": date}
        return self._make_request(endpoint, params)

    def get_coin_market_chart(self, coin_id: str, vs_currency: str, days: int) -> dict:
        """
        Get historical market data include price, market cap, and 24h volume.
        """
        endpoint = f"coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        return self._make_request(endpoint, params)

    def get_supported_vs_currencies(self) -> list[str]:
        """
        Get list of supported_vs_currencies.
        """
        endpoint = "simple/supported_vs_currencies"
        return self._make_request(endpoint)

    def get_top_coins(self, limit: int = 10, vs_currency: str = "usd") -> list[dict]:
        """
        Get the top N popular cryptocurrencies sorted by market cap.

        :param limit: Number of top coins to return (default: 10)
        :param vs_currency: The target currency of market data (default: "usd")
        :return: List of dictionaries containing coin data
        """
        endpoint = "coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False
        }
        response = self._make_request(endpoint, params)

        if isinstance(response, list):
            return [
                {
                    "id": coin["id"],
                    "symbol": coin["symbol"],
                    "name": coin["name"],
                    "current_price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "market_cap_rank": coin["market_cap_rank"],
                    "price_change_percentage_24h": coin["price_change_percentage_24h"]
                }
                for coin in response
            ]
        else:
            self.logger.error("Failed to fetch top coins")
            return []