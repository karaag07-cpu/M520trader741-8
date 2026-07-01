"""One-command Alpaca credentials/connectivity check.

Reads ALPACA_API_KEY / ALPACA_API_SECRET from the environment (or .env) and
verifies both the paper trading account endpoint and the market-data endpoint
the bot relies on. Prints a clear pass/fail summary and never echoes secrets.

Usage:
    python scripts/check_alpaca.py
"""

from __future__ import annotations

import os
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TRADING_URL = "https://paper-api.alpaca.markets/v2/account"
DATA_URL = "https://data.alpaca.markets/v2/stocks/AAPL/bars?timeframe=15Min&limit=5"


def _headers(key, secret):
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def main() -> int:
    key = os.environ.get("ALPACA_API_KEY", "").strip()
    secret = os.environ.get("ALPACA_API_SECRET", "").strip()

    if not key or not secret:
        print("❌ ALPACA_API_KEY / ALPACA_API_SECRET not set (check your .env).")
        return 1

    print(f"Using key ending in ...{key[-4:]}  (secret hidden)\n")
    ok = True

    # 1. Paper trading account
    try:
        r = requests.get(TRADING_URL, headers=_headers(key, secret), timeout=15)
        if r.status_code == 200:
            acct = r.json()
            print("✅ Trading account OK")
            print(f"   status={acct.get('status')}  buying_power={acct.get('buying_power')}"
                  f"  cash={acct.get('cash')}")
        else:
            ok = False
            print(f"❌ Trading account request failed: HTTP {r.status_code}")
            print(f"   {r.text[:200]}")
    except Exception as e:
        ok = False
        print(f"❌ Could not reach trading API: {e}")

    print()

    # 2. Market data (what the bot's fetchers use)
    try:
        r = requests.get(DATA_URL, headers=_headers(key, secret), timeout=15)
        if r.status_code == 200:
            bars = r.json().get("bars") or []
            print(f"✅ Market data OK — received {len(bars)} AAPL bars")
            if bars:
                last = bars[-1]
                print(f"   last bar: t={last.get('t')} close={last.get('c')}")
        else:
            ok = False
            print(f"❌ Market data request failed: HTTP {r.status_code}")
            print(f"   {r.text[:200]}")
    except Exception as e:
        ok = False
        print(f"❌ Could not reach market data API: {e}")

    print("\n" + ("✅ All checks passed — keys work." if ok else "❌ Some checks failed (see above)."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
