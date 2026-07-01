import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict
from signals.base_strategy import Signal, SignalType, Conviction
from risk.risk_manager import RiskManager

class BacktestTrader:
    def __init__(self, initial_balance: float = 100000.0, fee_pct: float = 0.001, slippage_pct: float = 0.0005):
        self.balance = initial_balance
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.positions = {} # symbol -> position_dict
        self.trade_history = []
        self.equity_curve = []

    def execute_signal(self, signal: Signal, price: float, timestamp: datetime):
        symbol = signal.symbol
        if symbol == "GLOBAL":
            return # Macro signal, not a trade

        # Apply slippage to entry
        if signal.type == SignalType.BUY:
            execution_price = price * (1 + self.slippage_pct)
            # Simple position sizing: use 10% of balance per trade
            amount = (self.balance * 0.1) / execution_price
            fee = self.balance * 0.1 * self.fee_pct
            self.balance -= fee
            
            self.positions[symbol] = {
                'side': 'BUY',
                'amount': amount,
                'entry_price': execution_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.tp_levels[0] if signal.tp_levels else None,
                'entry_time': timestamp
            }
        elif signal.type == SignalType.SELL:
            execution_price = price * (1 - self.slippage_pct)
            amount = (self.balance * 0.1) / execution_price
            fee = self.balance * 0.1 * self.fee_pct
            self.balance -= fee
            
            self.positions[symbol] = {
                'side': 'SELL',
                'amount': amount,
                'entry_price': execution_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.tp_levels[0] if signal.tp_levels else None,
                'entry_time': timestamp
            }

    def update(self, current_prices: Dict[str, float], timestamp: datetime):
        for symbol, pos in list(self.positions.items()):
            price = current_prices.get(symbol)
            if not price: continue

            closed = False
            close_reason = ""
            
            if pos['side'] == 'BUY':
                if pos['stop_loss'] and price <= pos['stop_loss']:
                    closed = True
                    close_reason = "STOP_LOSS"
                elif pos['take_profit'] and price >= pos['take_profit']:
                    closed = True
                    close_reason = "TAKE_PROFIT"
            else: # SELL
                if pos['stop_loss'] and price >= pos['stop_loss']:
                    closed = True
                    close_reason = "STOP_LOSS"
                elif pos['take_profit'] and price <= pos['take_profit']:
                    closed = True
                    close_reason = "TAKE_PROFIT"

            if closed:
                self._close_position(symbol, price, close_reason, timestamp)
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'balance': self.balance + self._get_unrealized_pnl(current_prices)
        })

    def _close_position(self, symbol, price, reason, timestamp):
        pos = self.positions.pop(symbol)
        
        # Apply slippage to exit
        if pos['side'] == 'BUY':
            exit_price = price * (1 - self.slippage_pct)
            pnl = (exit_price - pos['entry_price']) * pos['amount']
        else:
            exit_price = price * (1 + self.slippage_pct)
            pnl = (pos['entry_price'] - exit_price) * pos['amount']
        
        fee = (exit_price * pos['amount']) * self.fee_pct
        self.balance += pnl - fee
        
        trade_record = {
            **pos,
            'exit_price': exit_price,
            'exit_time': timestamp,
            'reason': reason,
            'pnl': pnl - fee
        }
        self.trade_history.append(trade_record)

    def _get_unrealized_pnl(self, current_prices):
        unrealized = 0
        for symbol, pos in self.positions.items():
            price = current_prices.get(symbol)
            if not price: continue
            if pos['side'] == 'BUY':
                unrealized += (price - pos['entry_price']) * pos['amount']
            else:
                unrealized += (pos['entry_price'] - price) * pos['amount']
        return unrealized

class BacktestEngine:
    def __init__(self, strategies: List, risk_manager: RiskManager = None, initial_capital: float = 100000.0):
        self.strategies = strategies
        self.risk_manager = risk_manager or RiskManager()
        self.trader = BacktestTrader(initial_balance=initial_capital)

    def run(self, data_df: pd.DataFrame, macro_data: List[Dict] = None):
        """
        data_df: Multi-asset OHLCV data. Assumes columns like (symbol, 'Close')
        macro_data: List of dicts with macro indicators aligned to timestamps
        """
        symbols = data_df.columns.get_level_values(0).unique()
        
        for i in range(50, len(data_df)): # Start with some history for indicators
            timestamp = data_df.index[i]
            current_prices = {sym: data_df.iloc[i][(sym, 'close')] for sym in symbols}
            
            # 1. Update existing positions
            self.trader.update(current_prices, timestamp)
            
            # 2. Get Macro Regime modifier (if any)
            macro_params = macro_data[i] if macro_data else {}
            macro_modifier = 1.0
            
            for strat in self.strategies:
                if strat.name == "MacroRegimeDetection":
                    macro_signal = strat.generate_signal(None, **macro_params)
                    macro_modifier = macro_signal.metadata.get('position_size_modifier', 1.0)
                    break
            
            # 3. Generate signals for each asset
            if macro_modifier > 0:
                for sym in symbols:
                    if sym in self.trader.positions: continue # Don't stack positions for now
                    
                    asset_history = data_df.iloc[:i+1][sym].copy()
                    # Preserve the symbol so strategies tag signals correctly;
                    # otherwise positions get keyed by a fallback name and never
                    # reconcile against current_prices in trader.update().
                    asset_history.attrs['symbol'] = sym

                    for strat in self.strategies:
                        if strat.name == "MacroRegimeDetection": continue
                        
                        signal = strat.generate_signal(asset_history)
                        if signal and signal.type != SignalType.NEUTRAL:
                            # 4. Enrich with RiskManager
                            levels = self.risk_manager.calculate_trade_levels(
                                signal.type.value, 
                                current_prices[sym]
                            )
                            signal.stop_loss = levels['stop_loss']
                            signal.tp_levels = levels['tp_levels']
                            
                            # 5. Execute
                            self.trader.execute_signal(signal, current_prices[sym], timestamp)
                            break # One strategy per asset per bar

        return self.calculate_metrics()

    def calculate_metrics(self):
        df_equity = pd.DataFrame(self.trader.equity_curve)
        if df_equity.empty:
            return {"error": "No trades executed"}
            
        returns = df_equity['balance'].pct_change().dropna()
        
        total_return = (df_equity['balance'].iloc[-1] / df_equity['balance'].iloc[0]) - 1
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6.5 * 4) if not returns.empty else 0 # Annualized 15m
        
        peak = df_equity['balance'].cummax()
        drawdown = (df_equity['balance'] - peak) / peak
        max_drawdown = drawdown.min()
        
        win_rate = 0
        if self.trader.trade_history:
            wins = [t for t in self.trader.trade_history if t['pnl'] > 0]
            win_rate = len(wins) / len(self.trader.trade_history)

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trader.trade_history)
        }
