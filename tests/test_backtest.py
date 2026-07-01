import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from backtest.engine import BacktestEngine, BacktestTrader
from signals.base_strategy import Signal, SignalType, Conviction, BaseStrategy


class MockStrategy(BaseStrategy):
    # The backtest engine feeds each strategy a single asset's history without
    # a symbol tag, so the fixture pins the symbol it is being tested against.
    SYMBOL = 'BTC/USDT'

    def generate_signal(self, data, **kwargs):
        if len(data) < 5:
            return None
        return Signal(
            symbol=self.SYMBOL,
            type=SignalType.BUY,
            timeframe='15m',
            conviction=Conviction.HIGH,
        )


def _make_multiindex_ohlcv(symbol, periods=100):
    dates = pd.date_range(start='2023-01-01', periods=periods, freq='15min')
    close = np.linspace(100.0, 150.0, periods)  # steadily rising -> hits take-profit
    cols = pd.MultiIndex.from_product([[symbol], ['open', 'high', 'low', 'close', 'volume']])
    df = pd.DataFrame(index=dates, columns=cols, dtype=float)
    df[(symbol, 'open')] = close
    df[(symbol, 'high')] = close * 1.001
    df[(symbol, 'low')] = close * 0.999
    df[(symbol, 'close')] = close
    df[(symbol, 'volume')] = 1000.0
    return df


class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        self.strategy = MockStrategy("Mock", "15m")
        # BacktestEngine builds its own RiskManager; 2nd positional is capital.
        self.engine = BacktestEngine([self.strategy], initial_capital=100000.0)
        self.data = _make_multiindex_ohlcv('BTC/USDT', periods=100)

    def test_backtest_run(self):
        results = self.engine.run(self.data)
        self.assertIn('total_return', results)
        # Rising prices should trigger take-profit exits, populating history.
        self.assertGreater(len(self.engine.trader.trade_history), 0)

    def test_trader_fees(self):
        # Entry fee model: fee = (balance * 0.1) * fee_pct is deducted on entry.
        trader = BacktestTrader(initial_balance=10000, fee_pct=0.01, slippage_pct=0.0)
        signal = Signal(symbol='BTC/USDT', type=SignalType.BUY, timeframe='15m',
                        conviction=Conviction.HIGH)
        trader.execute_signal(signal, price=100.0, timestamp=datetime(2023, 1, 1))
        # 10000 - (10000 * 0.1 * 0.01) = 9990.0
        self.assertEqual(trader.balance, 9990.0)
        self.assertIn('BTC/USDT', trader.positions)


if __name__ == '__main__':
    unittest.main()
