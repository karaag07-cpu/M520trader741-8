"""Print a MinuteTrader performance report.

Alpaca mode (trading.broker: alpaca): reports your live account — current
equity, open positions with unrealized P&L, and (best-effort) total return and
max drawdown from Alpaca's portfolio history.

Simulator mode: reports realized win rate / profit factor / drawdown from the
local paper-trading history (paper_state.json).

Usage:
    python scripts/report.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_loader import load_config
from analysis.performance import summarize_trades, equity_metrics, format_report


def _alpaca_report(config):
    from execution.alpaca_broker import AlpacaBroker
    alpaca_cfg = config.get('exchanges', {}).get('alpaca', {})
    if not (alpaca_cfg.get('api_key') and alpaca_cfg.get('api_secret')):
        print("Alpaca broker selected but no keys configured (.env).")
        return 1
    broker = AlpacaBroker(
        api_key=alpaca_cfg.get('api_key'),
        secret_key=alpaca_cfg.get('api_secret'),
        paper=alpaca_cfg.get('paper', True),
    )
    account = broker.get_account()
    positions = broker.get_positions()
    equity_curve = broker.get_portfolio_history()

    eq = equity_metrics(equity_curve) if equity_curve else None
    if eq is None:
        # Fall back to a single-point snapshot when history isn't available.
        eq = {'start': account['equity'], 'end': account['equity'], 'net_pnl': 0.0,
              'return_pct': 0.0, 'max_drawdown_pct': 0.0, 'points': 1}

    print(format_report(equity=eq))
    print(f"Cash:            ${account['cash']:,.2f}")
    print(f"Buying power:    ${account['buying_power']:,.2f}")
    print(f"Open positions:  {len(positions)}")
    total_unreal = 0.0
    for p in positions:
        total_unreal += p.get('unrealized_pnl', 0.0)
        print(f"  {p['symbol']:<10} {p['side']:<4} qty {abs(p['qty']):.6f}  "
              f"unrealized ${p.get('unrealized_pnl', 0.0):+,.2f}")
    if positions:
        print(f"Total unrealized P&L: ${total_unreal:+,.2f}")
    return 0


def _simulator_report():
    path = os.environ.get('MINUTETRADER_STATE_PATH', 'paper_state.json')
    if not os.path.exists(path):
        print("No paper-trading history yet (run the bot first).")
        return 0
    with open(path) as fh:
        state = json.load(fh)
    trades = state.get('trade_history', [])
    print(format_report(summary=summarize_trades(trades)))
    print(f"Current sim balance: ${float(state.get('balance', 0)):,.2f}")
    return 0


def main():
    config = load_config()
    broker = config.get('trading', {}).get('broker', 'paper')
    if broker == 'alpaca':
        return _alpaca_report(config)
    return _simulator_report()


if __name__ == "__main__":
    raise SystemExit(main())
