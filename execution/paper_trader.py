import json
import os
import tempfile

from utils.db_logger import log_trade_attempt


def default_state_path():
    """Where the paper trader persists its state between runs.

    ``$MINUTETRADER_STATE_PATH`` overrides; defaults to ``paper_state.json`` in
    the current working directory.
    """
    return os.environ.get('MINUTETRADER_STATE_PATH', 'paper_state.json')


class PaperTrader:
    def __init__(self, initial_balance=100000):
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []

    def committed_capital(self, exclude_symbol=None):
        """Total notional (at entry price) currently tied up in open positions.

        ``exclude_symbol`` omits one symbol from the total, used when placing a
        new order for a symbol whose existing position would be replaced.
        """
        return sum(
            pos['amount'] * pos['entry_price']
            for sym, pos in self.positions.items()
            if sym != exclude_symbol
        )

    def available_buying_power(self, exclude_symbol=None):
        """Cash not already committed to open positions."""
        return self.balance - self.committed_capital(exclude_symbol=exclude_symbol)

    def place_order(self, symbol, side, amount, price, stop_loss=None, take_profit=None):
        """
        Simulates placing an order and returns a trade record.
        """
        # Reject if the order would commit more capital than is still free,
        # accounting for notional already tied up in other open positions. An
        # existing position on this symbol would be replaced, so its committed
        # capital is excluded from the available total.
        total_cost = amount * price
        if total_cost > self.available_buying_power(exclude_symbol=symbol):
            log_trade_attempt(symbol, side, amount, price, "REJECTED", "Insufficient funds")
            return None

        trade = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'entry_price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': 'OPEN',
            'timestamp': 'now'
        }
        self.positions[symbol] = trade
        log_trade_attempt(symbol, side, amount, price, "EXECUTED", "Paper fill")
        return trade

    def update_positions(self, current_prices):
        """
        Updates open positions based on current prices, checking SL/TP.
        """
        for symbol, position in list(self.positions.items()):
            current_price = current_prices.get(symbol)
            if not current_price:
                continue
            
            # Check Stop Loss
            if position['side'] == 'BUY' and current_price <= position['stop_loss']:
                self._close_position(symbol, current_price, 'STOP_LOSS')
            elif position['side'] == 'SELL' and current_price >= position['stop_loss']:
                self._close_position(symbol, current_price, 'STOP_LOSS')
            
            # Check Take Profit
            elif position['side'] == 'BUY' and current_price >= position['take_profit']:
                self._close_position(symbol, current_price, 'TAKE_PROFIT')
            elif position['side'] == 'SELL' and current_price <= position['take_profit']:
                self._close_position(symbol, current_price, 'TAKE_PROFIT')

    def close_all_positions(self, current_prices=None, reason='KILL_SWITCH'):
        """Flatten every open position. Used by the kill switch to ensure no
        position is left unmanaged when trading halts.

        Positions are closed at the supplied current price; if a price is not
        available for a symbol, the position is closed at its entry price
        (realising zero P&L) so nothing is left open. Returns the number of
        positions closed.
        """
        current_prices = current_prices or {}
        count = 0
        for symbol, position in list(self.positions.items()):
            close_price = current_prices.get(symbol, position['entry_price'])
            self._close_position(symbol, close_price, reason)
            count += 1
        return count

    def _close_position(self, symbol, close_price, reason):
        position = self.positions.pop(symbol)
        position['close_price'] = close_price
        position['status'] = 'CLOSED'
        position['close_reason'] = reason
        
        # Calculate P&L
        if position['side'] == 'BUY':
            pnl = (close_price - position['entry_price']) * position['amount']
        else:
            pnl = (position['entry_price'] - close_price) * position['amount']
        
        position['pnl'] = pnl
        self.balance += pnl
        self.trade_history.append(position)
        print(f"Closed {symbol} {position['side']} at {close_price} Reason: {reason} PnL: {pnl}")

    def get_portfolio_value(self, current_prices):
        """Total account value: cash balance plus the unrealised P&L of every
        open position marked to the current market price."""
        total_value = self.balance
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol)
            if price is None:
                continue
            if position['side'] == 'BUY':
                total_value += (price - position['entry_price']) * position['amount']
            else:
                total_value += (position['entry_price'] - price) * position['amount']
        return total_value

    # -- persistence -----------------------------------------------------
    def to_dict(self):
        """Serialize account state to a JSON-safe dict."""
        return {
            'balance': self.balance,
            'positions': self.positions,
            'trade_history': self.trade_history,
        }

    def load_dict(self, data):
        """Restore account state from a dict produced by ``to_dict``."""
        self.balance = data.get('balance', self.balance)
        self.positions = data.get('positions', {}) or {}
        self.trade_history = data.get('trade_history', []) or []

    def save_state(self, path=None):
        """Atomically persist state so positions/balance survive restarts."""
        path = path or default_state_path()
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory or '.', suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as fh:
                json.dump(self.to_dict(), fh, indent=2, default=str)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return path

    def load_state(self, path=None):
        """Load persisted state if the file exists; returns True if loaded."""
        path = path or default_state_path()
        if not os.path.exists(path):
            return False
        with open(path) as fh:
            self.load_dict(json.load(fh))
        return True
