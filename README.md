# tradeBotBinace — Binance Futures Testnet Trading Bot

A simple, well-structured Python trading bot that places **MARKET** and **LIMIT** orders on the [Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M perpetuals) via the REST API.

---

## Project Structure

```
tradeBotBinace/
├── trading_bot/
│   ├── __init__.py
│   ├── cli.py               # CLI entry point (argparse)
│   └── bot/
│       ├── __init__.py
│       ├── client.py        # Binance Futures REST API wrapper
│       ├── orders.py        # Order placement logic + output formatting
│       ├── validators.py    # Input validation helpers
│       └── logging_config.py# Structured logging (console + rotating file)
├── logs/
│   ├── market_order.log     # Sample MARKET order log
│   └── limit_order.log      # Sample LIMIT order log
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.8+
- `requests` library

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/tamo2005/tradeBotBinace.git
cd tradeBotBinace
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate.bat     # Windows CMD
# .venv\Scripts\Activate.ps1     # Windows PowerShell
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Obtain Binance Futures Testnet API credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com).
2. Log in or register (GitHub OAuth is supported).
3. Navigate to **API Key** and generate a key pair.
4. Copy your **API Key** and **Secret Key**.

### 5. Configure credentials

**Option A - environment variables (recommended)**

Linux/macOS:

```bash
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_api_secret_here"
```

Windows PowerShell:

```powershell
$env:BINANCE_API_KEY="your_api_key_here"
$env:BINANCE_API_SECRET="your_api_secret_here"
```

Windows CMD:

```cmd
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

**Option B — pass directly on the command line**

```bash
python -m trading_bot.cli --api-key KEY --api-secret SECRET ...
```

> ⚠️  Never commit your API credentials to version control.

---

## How to Run

Run commands from the repository root directory (`tradeBotBinace`).

### General syntax

```bash
python -m trading_bot.cli \
  --symbol SYMBOL \
  --side SIDE \
  --type TYPE \
  --quantity QTY \
  [--price PRICE] \
  [--log-level LEVEL]
```

Parameter notes:
- `--symbol`: e.g. `BTCUSDT`
- `--side`: `BUY` or `SELL`
- `--type`: `MARKET` or `LIMIT` (alias: `--order-type`)
- `--quantity`: positive number
- `--price`: required for `LIMIT`, ignored for `MARKET`
- `--log-level`: `DEBUG`, `INFO` (default), `WARNING`, `ERROR`

### Example — Market BUY order

```bash
python -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

**Expected output:**

```
=======================================================
  ORDER REQUEST SUMMARY
=======================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
=======================================================

=======================================================
  ORDER RESPONSE
=======================================================
  Order ID   : 4285817839
  Status     : FILLED
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Orig Qty   : 0.001
  Exec Qty   : 0.001
  Avg Price  : 83512.40000
  Price      : 0
  Time       : 1744624523899
=======================================================

✅  Order placed successfully (status: FILLED)
```

### Example — Limit SELL order

```bash
python -m trading_bot.cli \
  --symbol ETHUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.01 \
  --price 3000
```

**Expected output:**

```
=======================================================
  ORDER REQUEST SUMMARY
=======================================================
  Symbol     : ETHUSDT
  Side       : SELL
  Type       : LIMIT
  Quantity   : 0.01
  Price      : 3000.0
=======================================================

=======================================================
  ORDER RESPONSE
=======================================================
  Order ID   : 1823904571
  Status     : NEW
  Symbol     : ETHUSDT
  Side       : SELL
  Type       : LIMIT
  Orig Qty   : 0.01
  Exec Qty   : 0
  Avg Price  : 0.00000
  Price      : 3000.00
  Time       : 1744624967445
=======================================================

✅  Order placed successfully (status: NEW)
```

### Example — verbose debug logging

```bash
python -m trading_bot.cli \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001 \
  --log-level DEBUG
```

---

## Logging

All API requests, responses, and errors are logged to:

- **Console** — at the chosen log level (default: INFO).
- **File** — `logs/trading_bot.log` at DEBUG level (5 MB rotating, 5 backups).

Sample log files are included in the `logs/` directory:

| File | Description |
|------|-------------|
| `logs/market_order.log` | MARKET BUY on BTCUSDT |
| `logs/limit_order.log`  | LIMIT SELL on ETHUSDT  |

---

## Error Handling

| Situation | Behaviour |
|-----------|-----------|
| Missing credentials | Exits with clear message and exit code 1 |
| Invalid symbol / side / type | Validation error printed, exit code 1 |
| Missing price for LIMIT order | Validation error printed, exit code 1 |
| Binance API error (e.g. -1121) | Error code + message printed, exit code 2 |
| Network failure / timeout | Exception logged and printed, exit code 3 |

## Troubleshooting

- Error `-2015` (`Invalid API-key, IP, or permissions for action`):
  - Make sure keys were created on Binance Futures Testnet: https://testnet.binancefuture.com
  - Verify API key permissions allow Futures trading actions on testnet
  - If IP restriction is enabled, add your current public IP or disable restriction for testing
  - Regenerate a fresh testnet key pair and retry
- Error `ModuleNotFoundError: No module named 'trading_bot'`:
  - Run commands from the repository root folder (`tradeBotBinace`)
  - Example: `cd tradeBotBinace` then run `python -m trading_bot.cli ...`

---

## Assumptions

- Only **USDT-M perpetual contracts** are supported (symbols must end in `USDT`).
- All requests go to the **Binance Futures Testnet** (`https://testnet.binancefuture.com`).
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default.
- Quantity precision requirements depend on the symbol; the Binance API will reject orders that violate exchange filters (e.g. `LOT_SIZE`).
- No position management or risk controls are implemented — this is an order-placement utility only.

---

## Bonus Features

- **Structured, reusable code** — separate layers for API client, order logic, validation, and CLI.
- **Rotating log files** — prevents unbounded disk usage.
- **`--log-level` flag** — switch to `DEBUG` to see full request/response payloads for troubleshooting.
