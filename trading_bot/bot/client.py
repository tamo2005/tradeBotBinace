"""
Binance Futures Testnet REST API client wrapper.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"
_DEFAULT_RECV_WINDOW = 5000
_REQUEST_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Lightweight wrapper around the Binance Futures Testnet REST API.

    Only signed (account) endpoints are used for order placement.
    """

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append HMAC-SHA256 signature to the parameter dictionary."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _get_timestamp(self) -> int:
        """Return current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = True,
    ) -> Any:
        """
        Execute an HTTP request against the Binance Futures Testnet.

        Args:
            method:  HTTP method ('GET', 'POST', 'DELETE', …).
            path:    API endpoint path (e.g. '/fapi/v1/order').
            params:  Query / body parameters.
            signed:  Whether to add timestamp + signature.

        Returns:
            Parsed JSON response body.

        Raises:
            BinanceAPIError: On non-zero Binance error codes.
            requests.RequestException: On network-level failures.
        """
        params = dict(params or {})

        if signed:
            params["timestamp"] = self._get_timestamp()
            params["recvWindow"] = _DEFAULT_RECV_WINDOW
            params = self._sign(params)

        url = BASE_URL + path

        log_params = dict(params)
        if "signature" in log_params:
            log_params["signature"] = "***"

        logger.debug("API request  → %s %s | params: %s", method, url, log_params)

        try:
            if method.upper() in ("GET", "DELETE"):
                response = self._session.request(
                    method, url, params=params, timeout=_REQUEST_TIMEOUT
                )
            else:
                response = self._session.request(
                    method, url, data=params, timeout=_REQUEST_TIMEOUT
                )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out after %s seconds: %s", _REQUEST_TIMEOUT, exc)
            raise

        logger.debug(
            "API response ← %s %s | status: %s | body: %s",
            method,
            url,
            response.status_code,
            response.text,
        )

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            # Binance uses negative codes for errors
            if int(data["code"]) < 0:
                logger.error(
                    "Binance API error | code=%s | msg=%s", data["code"], data.get("msg")
                )
                raise BinanceAPIError(int(data["code"]), data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return server time in milliseconds (useful for clock-sync checks)."""
        data = self._request("GET", "/fapi/v1/time", signed=False)
        return data["serverTime"]

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> dict:
        """
        Place a Futures order (MARKET or LIMIT).

        Args:
            symbol:        Trading pair (e.g. 'BTCUSDT').
            side:          'BUY' or 'SELL'.
            order_type:    'MARKET' or 'LIMIT'.
            quantity:      Contract quantity.
            price:         Limit price (required for LIMIT orders).
            time_in_force: 'GTC', 'IOC', or 'FOK' (LIMIT orders only).
            reduce_only:   Whether the order can only reduce a position.

        Returns:
            Parsed JSON response from Binance.

        Raises:
            BinanceAPIError: When Binance returns an API-level error.
            requests.RequestException: On network failures.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        params["newOrderRespType"] = "RESULT"

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if reduce_only:
            params["reduceOnly"] = "true"

        logger.info(
            "Placing %s %s order | symbol=%s | qty=%s | price=%s",
            side,
            order_type,
            symbol,
            quantity,
            price if price is not None else "MARKET",
        )

        return self._request("POST", "/fapi/v1/order", params=params)
