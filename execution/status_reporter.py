"""Serialize live bot state to JSON for the website dashboard to read.

The trading bot and the website are separate processes, so the bot publishes a
small ``status.json`` snapshot each cycle and the site reads it. Kept pure and
dependency-free (stdlib only) so it's easy to test.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone


def default_status_path():
    """Where to publish status.json.

    ``$MINUTETRADER_STATUS_PATH`` overrides; otherwise ``website/status.json``
    at the project root, which the site's dashboard reads at request time.
    """
    return os.environ.get('MINUTETRADER_STATUS_PATH') or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'website', 'status.json'
    )


def _unrealized_pnl(position, price):
    if position['side'] == 'BUY':
        return (price - position['entry_price']) * position['amount']
    return (position['entry_price'] - price) * position['amount']


def build_status(paper_trader, prices=None, regime=None, updated_at=None):
    """Build a JSON-serializable snapshot of the trader's current state."""
    prices = prices or {}
    positions = []
    for symbol, pos in paper_trader.positions.items():
        price = prices.get(symbol, pos['entry_price'])
        positions.append({
            'symbol': symbol,
            'side': pos['side'],
            'amount': pos['amount'],
            'entry_price': pos['entry_price'],
            'current_price': price,
            'stop_loss': pos.get('stop_loss'),
            'take_profit': pos.get('take_profit'),
            'unrealized_pnl': _unrealized_pnl(pos, price),
        })

    return {
        'updated_at': updated_at or datetime.now(timezone.utc).isoformat(),
        'balance': paper_trader.balance,
        'portfolio_value': paper_trader.get_portfolio_value(prices),
        'committed_capital': paper_trader.committed_capital(),
        'available_buying_power': paper_trader.available_buying_power(),
        'open_positions': positions,
        'open_position_count': len(positions),
        'closed_trades': len(paper_trader.trade_history),
        'regime': regime or {},
        'source': 'simulator',
    }


def build_alpaca_status(account, positions, regime=None, updated_at=None):
    """Build the dashboard snapshot from a live Alpaca account + positions.

    ``account`` is AlpacaBroker.get_account() and ``positions`` is
    AlpacaBroker.get_positions(). Produces the same shape as ``build_status``
    so the dashboard renders identically whether the source is the simulator
    or the real Alpaca account.
    """
    open_positions = []
    committed = 0.0
    for p in positions:
        amount = abs(p.get('qty', 0))
        entry = p.get('entry_price', 0)
        committed += amount * entry
        open_positions.append({
            'symbol': p['symbol'],
            'side': p['side'],
            'amount': amount,
            'entry_price': entry,
            'current_price': p.get('current_price', 0),
            'stop_loss': None,
            'take_profit': None,
            'unrealized_pnl': p.get('unrealized_pnl', 0),
        })

    portfolio_value = account.get('portfolio_value') or account.get('equity', 0)
    return {
        'updated_at': updated_at or datetime.now(timezone.utc).isoformat(),
        'balance': account.get('cash', 0),
        'portfolio_value': portfolio_value,
        'committed_capital': committed,
        'available_buying_power': account.get('buying_power', 0),
        'open_positions': open_positions,
        'open_position_count': len(open_positions),
        'closed_trades': 0,
        'regime': regime or {},
        'source': 'alpaca',
    }


def write_status(status, path=None):
    """Atomically write ``status`` as JSON to ``path`` (default status path)."""
    path = path or default_status_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    # Write to a temp file then replace, so readers never see a partial file.
    fd, tmp = tempfile.mkstemp(dir=directory or '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as fh:
            json.dump(status, fh, indent=2, default=str)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return path
