"""Reconcile the bot's positions against a real broker snapshot.

The bot's paper positions can drift from what a broker (e.g. Webull) actually
holds. Since Webull has no official market API, reconciliation reads a broker
*snapshot* — a small JSON file you export or maintain — and diffs it against
the bot's open positions, reporting anything out of sync.

Snapshot format (either form accepted)::

    {"positions": [{"symbol": "BTC/USD", "qty": 0.05},
                   {"symbol": "AAPL", "amount": 10, "side": "SELL"}]}

or just a bare list of those position objects. ``qty`` may be signed
(negative = short); alternatively give ``amount`` + ``side``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone


def default_snapshot_path():
    return os.environ.get('MINUTETRADER_BROKER_SNAPSHOT', 'broker_snapshot.json')


def load_broker_snapshot(path=None):
    """Load a broker snapshot file; returns its position list or None."""
    path = path or default_snapshot_path()
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return data.get('positions', [])
    return data or []


def _signed_qty(side, amount):
    return amount if str(side).upper() == 'BUY' else -amount


def _broker_map(positions):
    """Normalise broker snapshot positions to {symbol: signed_qty}."""
    out = {}
    for p in positions or []:
        symbol = p.get('symbol')
        if symbol is None:
            continue
        if 'qty' in p and p['qty'] is not None:
            out[symbol] = float(p['qty'])
        else:
            out[symbol] = _signed_qty(p.get('side', 'BUY'), float(p.get('amount', 0)))
    return out


def _bot_map(bot_positions):
    """Normalise the paper trader's positions dict to {symbol: signed_qty}."""
    out = {}
    for symbol, pos in bot_positions.items():
        out[symbol] = _signed_qty(pos['side'], float(pos['amount']))
    return out


def reconcile(bot_positions, broker_positions, tolerance=1e-6):
    """Diff bot vs broker positions and report discrepancies.

    Returns a JSON-serializable dict with ``in_sync`` plus the matched,
    only-in-bot, only-in-broker, and quantity-mismatch breakdowns.
    """
    bot = _bot_map(bot_positions)
    broker = _broker_map(broker_positions)

    matched, only_in_bot, only_in_broker, mismatch = [], [], [], []
    for symbol in sorted(set(bot) | set(broker)):
        in_bot, in_broker = symbol in bot, symbol in broker
        if in_bot and in_broker:
            if abs(bot[symbol] - broker[symbol]) <= tolerance:
                matched.append({'symbol': symbol, 'qty': bot[symbol]})
            else:
                mismatch.append({'symbol': symbol, 'bot_qty': bot[symbol], 'broker_qty': broker[symbol]})
        elif in_bot:
            only_in_bot.append({'symbol': symbol, 'bot_qty': bot[symbol]})
        else:
            only_in_broker.append({'symbol': symbol, 'broker_qty': broker[symbol]})

    return {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'in_sync': not (only_in_bot or only_in_broker or mismatch),
        'matched': matched,
        'only_in_bot': only_in_bot,
        'only_in_broker': only_in_broker,
        'quantity_mismatch': mismatch,
    }


def reconcile_paper_trader(paper_trader, snapshot_path=None):
    """Reconcile a paper trader against the snapshot file, or None if absent."""
    positions = load_broker_snapshot(snapshot_path)
    if positions is None:
        return None
    return reconcile(paper_trader.positions, positions)
