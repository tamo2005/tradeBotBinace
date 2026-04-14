"""
Order placement logic — high-level wrapper over the Binance client.
"""

from __future__ import annotations

import logging

from trading_bot.bot.client import BinanceAPIError, BinanceClient
from trading_bot.bot.validators import validate_all

logger = logging.getLogger("trading_bot.orders")


def _format_order_summary(params: dict) -> str:
    """Return a human-readable summary of the order parameters."""
    lines = [
        "=" * 55,
        "  ORDER REQUEST SUMMARY",
        "=" * 55,
        f"  Symbol     : {params['symbol']}",
        f"  Side       : {params['side']}",
        f"  Type       : {params['order_type']}",
        f"  Quantity   : {params['quantity']}",
    ]
    if params.get("price") is not None:
        lines.append(f"  Price      : {params['price']}")
    lines.append("=" * 55)
    return "\n".join(lines)


def _format_order_response(response: dict) -> str:
    """Return a human-readable representation of the Binance order response."""
    lines = [
        "=" * 55,
        "  ORDER RESPONSE",
        "=" * 55,
        f"  Order ID   : {response.get('orderId', 'N/A')}",
        f"  Status     : {response.get('status', 'N/A')}",
        f"  Symbol     : {response.get('symbol', 'N/A')}",
        f"  Side       : {response.get('side', 'N/A')}",
        f"  Type       : {response.get('type', 'N/A')}",
        f"  Orig Qty   : {response.get('origQty', 'N/A')}",
        f"  Exec Qty   : {response.get('executedQty', 'N/A')}",
        f"  Avg Price  : {response.get('avgPrice', 'N/A')}",
        f"  Price      : {response.get('price', 'N/A')}",
        f"  Time       : {response.get('updateTime', 'N/A')}",
        "=" * 55,
    ]
    return "\n".join(lines)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
) -> dict:
    """
    Validate inputs and place a Futures order on Binance Testnet.

    Args:
        client:     Initialised BinanceClient instance.
        symbol:     Trading pair symbol (e.g. 'BTCUSDT').
        side:       'BUY' or 'SELL'.
        order_type: 'MARKET' or 'LIMIT'.
        quantity:   Number of contracts.
        price:      Limit price (required for LIMIT, ignored for MARKET).

    Returns:
        Parsed Binance API response dictionary.

    Raises:
        ValueError:      On invalid input parameters.
        BinanceAPIError: On Binance API-level errors.
        Exception:       On unexpected errors.
    """
    # 1. Validate
    params = validate_all(symbol, side, order_type, quantity, price)

    # 2. Print order summary
    summary = _format_order_summary(params)
    print(summary)
    logger.info("Order summary:\n%s", summary)

    # 3. Place order via client
    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
        )
    except BinanceAPIError as exc:
        logger.error("Order failed | %s", exc)
        print(f"\n❌  Order FAILED — Binance API error {exc.code}: {exc.message}\n")
        raise
    except Exception as exc:
        logger.exception("Unexpected error while placing order: %s", exc)
        print(f"\n❌  Order FAILED — unexpected error: {exc}\n")
        raise

    # 4. Print response
    response_text = _format_order_response(response)
    print(response_text)
    logger.info("Order response:\n%s", response_text)

    status = response.get("status", "UNKNOWN")
    if status in ("FILLED", "NEW", "PARTIALLY_FILLED"):
        print(f"\n✅  Order placed successfully (status: {status})\n")
        logger.info("Order placed successfully | orderId=%s | status=%s", response.get("orderId"), status)
    else:
        print(f"\n⚠️   Order submitted with status: {status}\n")
        logger.warning("Unexpected order status: %s | response: %s", status, response)

    return response
