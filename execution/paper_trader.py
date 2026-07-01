from utils.db_logger import log_trade_attempt

class PaperTrader:
    def __init__(self, initial_balance=100000):
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []

    def place_order(self, symbol, side, amount, price, stop_loss=None, take_profit=None):
        """
        Simulates placing an order and returns a trade record.
        """
        # Check if we have enough balance
        total_cost = amount * price
        if total_cost > self.balance:
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
        total_value = self.balance
        # In a real implementation, add current value of open positions
        return total_value
