import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest.engine import BacktestEngine, BacktestTrader
from signals.base_strategy import Signal, SignalType, Conviction, BaseStrategy
from risk.risk_manager import RiskManager

class MockStrategy(BaseStrategy):
    def generate_signal(self, data, **kwargs):
        if len(data) < 5: return None
        return Signal(
            symbol=data.attrs.get('symbol', 'TEST'),
            type=SignalType.BUY,
            timeframe='15m',
            conviction=Conviction.HIGH
        )

class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        self.risk_manager = RiskManager()
        self.strategy = MockStrategy("Mock", "15m")
        self.engine = BacktestEngine([self.strategy], self.risk_manager)
        
        # Create dummy data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='15min')
        self.data = pd.DataFrame({
            'open': np.linspace(100, 110, 100),
            'high': np.linspace(101, 111, 100),
            'low': np.linspace(99, 109, 100),
            'close': np.linspace(100.5, 110.5, 100),
            'volume': [1000] * 100
        }, index=dates)
        self.data.attrs['symbol'] = 'BTC/USDT'

    def test_backtest_run(self):
        results = self.engine.run({'BTC/USDT': self.data})
        self.assertIn('total_return', results)
        self.assertGreater(len(self.engine.trader.trade_history), 0)

    def test_trader_fees(self):
        trader = BacktestTrader(initial_balance=10000, fee_pct=0.01, slippage_pct=0.0)
        trader.place_order('BTC/USDT', 'BUY', 1.0, 100.0)
        # 10000 - (1.0 * 100.0 * 0.01) = 9999
        self.assertEqual(trader.balance, 9999.0)

if __name__ == '__main__':
    unittest.main()
