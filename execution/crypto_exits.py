"""Software stop-loss / take-profit for crypto positions on Alpaca.

Alpaca supports bracket orders for equities (Alpaca auto-manages the exit) but
NOT for crypto. So for crypto the bot tracks each position's stop/target itself,
persists them, and closes the position when a level is touched.

Symbols are normalised (slashes stripped) so an order symbol like ``ETH/USD``
matches an Alpaca position symbol like ``ETHUSD``.
"""

from __future__ import annotations

import json
import os
import tempfile


def default_exits_path():
    return os.environ.get('MINUTETRADER_CRYPTO_EXITS_PATH', 'crypto_exits.json')


def _norm(symbol):
    return str(symbol).replace('/', '').upper()


class CryptoExitTracker:
    def __init__(self, path=None):
        self.path = path or default_exits_path()
        self.brackets = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as fh:
                    self.brackets = json.load(fh)
            except (ValueError, OSError):
                self.brackets = {}

    def _save(self):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory or '.', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as fh:
                json.dump(self.brackets, fh, indent=2)
            os.replace(tmp, self.path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def record(self, symbol, side, stop_loss, take_profit):
        """Remember the stop/target for a crypto position."""
        self.brackets[_norm(symbol)] = {
            'side': str(side).upper(),
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
        }
        self._save()

    def discard(self, symbol):
        if self.brackets.pop(_norm(symbol), None) is not None:
            self._save()

    def positions_to_close(self, positions):
        """Given Alpaca positions (with current_price), return [(symbol, reason)]
        for those whose tracked stop-loss or take-profit has been touched.

        Only positions we're tracking are considered; the returned symbol is the
        position's own symbol (as Alpaca reports it) so it can be closed directly.
        """
        to_close = []
        for pos in positions:
            key = _norm(pos.get('symbol'))
            bracket = self.brackets.get(key)
            if not bracket:
                continue
            price = pos.get('current_price')
            if not price:
                continue
            side = bracket['side']
            stop, target = bracket['stop_loss'], bracket['take_profit']
            if side == 'BUY':
                if price <= stop:
                    to_close.append((pos['symbol'], 'stop_loss'))
                elif price >= target:
                    to_close.append((pos['symbol'], 'take_profit'))
            else:  # short
                if price >= stop:
                    to_close.append((pos['symbol'], 'stop_loss'))
                elif price <= target:
                    to_close.append((pos['symbol'], 'take_profit'))
        return to_close
