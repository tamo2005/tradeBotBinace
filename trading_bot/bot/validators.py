"""
Input validation for CLI parameters.
"""

from __future__ import annotations

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}

# Commonly traded Binance Futures USDT-M symbols (non-exhaustive; basic check only)
_SYMBOL_SUFFIX = "USDT"


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalise the trading symbol.

    Rules:
    - Must be a non-empty alphanumeric string.
    - Must end with 'USDT' (USDT-M perpetual contracts only).

    Returns:
        Normalised upper-case symbol string.

    Raises:
        ValueError: When the symbol is invalid.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol must not be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' must be alphanumeric (e.g. BTCUSDT).")
    if not symbol.endswith(_SYMBOL_SUFFIX):
        raise ValueError(
            f"Symbol '{symbol}' must end with 'USDT' for USDT-M futures (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """
    Validate the order side.

    Returns:
        Upper-case side string ('BUY' or 'SELL').

    Raises:
        ValueError: When the side is not BUY or SELL.
    """
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate the order type.

    Returns:
        Upper-case order type string ('MARKET' or 'LIMIT').

    Raises:
        ValueError: When the order type is unsupported.
    """
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> float:
    """
    Validate the order quantity.

    Returns:
        Positive float quantity.

    Raises:
        ValueError: When the quantity is not a positive number.
    """
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' must be a valid positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: str | float | None, order_type: str) -> float | None:
    """
    Validate the order price.

    - Required for LIMIT orders.
    - Must be None / omitted for MARKET orders.

    Returns:
        Positive float price, or None for MARKET orders.

    Raises:
        ValueError: When the price is missing for LIMIT or invalid.
    """
    order_type = order_type.strip().upper()

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Price '{price}' must be a valid positive number.")
        if p <= 0:
            raise ValueError(f"Price must be greater than zero, got {p}.")
        return p

    # MARKET — price should not be provided
    if price is not None:
        try:
            p = float(price)
            if p != 0:
                raise ValueError(
                    "Price should not be specified for MARKET orders "
                    "(it is determined by the market)."
                )
        except (TypeError, ValueError) as exc:
            raise ValueError(str(exc)) from exc

    return None


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: str | float | None = None,
) -> dict:
    """
    Run all validations and return a clean parameter dictionary.

    Returns:
        Dict with keys: symbol, side, order_type, quantity, price.

    Raises:
        ValueError: On the first validation failure encountered.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_order_type = validate_order_type(order_type)
    clean_quantity = validate_quantity(quantity)
    clean_price = validate_price(price, clean_order_type)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_order_type,
        "quantity": clean_quantity,
        "price": clean_price,
    }
