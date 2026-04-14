"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:

  # Market BUY
  python -m trading_bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit SELL
  python -m trading_bot.cli --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000

Environment variables:
  BINANCE_API_KEY     – your Binance Futures Testnet API key
  BINANCE_API_SECRET  – your Binance Futures Testnet API secret
"""

from __future__ import annotations

import argparse
import os
import sys

from trading_bot.bot.client import BinanceAPIError, BinanceClient
from trading_bot.bot.logging_config import setup_logging
from trading_bot.bot.orders import place_order
from trading_bot.bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Market BUY:
    python -m trading_bot.cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  Limit SELL:
    python -m trading_bot.cli --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000

  Using explicit API credentials:
    python -m trading_bot.cli --api-key KEY --api-secret SECRET \\
        --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Environment variables (alternative to --api-key / --api-secret):
  BINANCE_API_KEY
  BINANCE_API_SECRET
""",
    )

    # Credentials
    cred_group = parser.add_argument_group("API credentials")
    cred_group.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_API_KEY"),
        metavar="KEY",
        help="Binance Futures Testnet API key "
             "(default: $BINANCE_API_KEY environment variable).",
    )
    cred_group.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_API_SECRET"),
        metavar="SECRET",
        help="Binance Futures Testnet API secret "
             "(default: $BINANCE_API_SECRET environment variable).",
    )

    # Order parameters
    order_group = parser.add_argument_group("Order parameters")
    order_group.add_argument(
        "--symbol",
        required=True,
        metavar="SYMBOL",
        help="Trading pair symbol, e.g. BTCUSDT.",
    )
    order_group.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL"],
        metavar="SIDE",
        help="Order side: BUY or SELL.",
    )
    order_group.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT"],
        metavar="TYPE",
        help="Order type: MARKET or LIMIT.",
    )
    order_group.add_argument(
        "--quantity",
        required=True,
        metavar="QTY",
        help="Order quantity (number of contracts).",
    )
    order_group.add_argument(
        "--price",
        default=None,
        metavar="PRICE",
        help="Limit price (required for LIMIT orders, ignored for MARKET).",
    )

    # Misc
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )

    return parser


def _validate_args(args: argparse.Namespace) -> dict:
    """
    Validate parsed CLI arguments and return a clean parameter dict.

    Exits with a non-zero status code and prints a helpful message on error.
    """
    errors: list[str] = []

    # Symbol
    try:
        symbol = validate_symbol(args.symbol)
    except ValueError as exc:
        errors.append(f"--symbol: {exc}")
        symbol = ""

    # Side
    try:
        side = validate_side(args.side)
    except ValueError as exc:
        errors.append(f"--side: {exc}")
        side = ""

    # Order type
    try:
        order_type = validate_order_type(args.order_type)
    except ValueError as exc:
        errors.append(f"--type: {exc}")
        order_type = ""

    # Quantity
    try:
        quantity = validate_quantity(args.quantity)
    except ValueError as exc:
        errors.append(f"--quantity: {exc}")
        quantity = 0.0

    # Price (only validate fully if order_type was valid)
    price = None
    if order_type:
        try:
            price = validate_price(args.price, order_type)
        except ValueError as exc:
            errors.append(f"--price: {exc}")

    if errors:
        print("\n❌  Input validation failed:\n")
        for err in errors:
            print(f"    • {err}")
        print()
        sys.exit(1)

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
    }


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Set up logging early
    logger = setup_logging(args.log_level)
    logger.debug("Parsed CLI arguments: %s", vars(args))

    # Validate credentials
    if not args.api_key or not args.api_secret:
        print(
            "\n❌  API credentials are required.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "    or pass --api-key and --api-secret on the command line.\n"
        )
        sys.exit(1)

    # Validate order parameters
    params = _validate_args(args)

    # Build client and place order
    client = BinanceClient(api_key=args.api_key, api_secret=args.api_secret)

    try:
        place_order(
            client=client,
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
        )
    except (BinanceAPIError, ValueError) as exc:
        logger.error("Order failed: %s", exc)
        sys.exit(2)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        sys.exit(3)


if __name__ == "__main__":
    main()
