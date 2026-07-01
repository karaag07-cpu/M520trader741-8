import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from backtest.engine import BacktestEngine, BacktestTrader
from signals.base_strategy import Signal, SignalType, Conviction, BaseStrategy
from risk.risk_manager import RiskManager


class MockStrategy(BaseStrategy):
    def generate_signal(self, data, **kwargs):
        if len(data) < 5:
            return None
        return Signal(
            symbol=data.attrs.get('symbol', 'TEST'),
            type=SignalType.BUY,
            timeframe='15m',
            conviction=Conviction.HIGH
        )


def _make_multiindex_ohlcv(symbol='BTC/USDT', periods=100):
    """Build the (symbol, field) MultiIndex-column frame BacktestEngine.run expects.

    Matches the shape produced by backtest/run_backtest.py, which is the real
    entry point the engine is designed around.
    """
    dates = pd.date_range(start='2023-01-01', periods=periods, freq='15min')
    df = pd.DataFrame({
        'open': np.linspace(100, 110, periods),
        'high': np.linspace(101, 111, periods),
        'low': np.linspace(99, 109, periods),
        'close': np.linspace(100.5, 110.5, periods),
        'volume': [1000] * periods,
    }, index=dates)
    df.columns = pd.MultiIndex.from_product([[symbol], df.columns])
    return df


class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        self.risk_manager = RiskManager()
        self.strategy = MockStrategy("Mock", "15m")
        self.engine = BacktestEngine([self.strategy], self.risk_manager)
        self.data = _make_multiindex_ohlcv('BTC/USDT', periods=100)

    def test_backtest_run(self):
        results = self.engine.run(self.data)
        self.assertIn('total_return', results)
        # With the symbol now propagated onto per-asset history, signals are
        # tagged 'BTC/USDT', positions reconcile in update(), and rising prices
        # trip the take-profit so closed trades land in trade_history.
        self.assertGreater(len(self.engine.trader.trade_history), 0)
        for trade in self.engine.trader.trade_history:
            self.assertEqual(trade['side'], 'BUY')

    def test_injected_risk_manager_is_used(self):
        # The engine should use the risk manager it is given, not a fresh one.
        self.assertIs(self.engine.risk_manager, self.risk_manager)

    def test_trader_fees(self):
        # execute_signal is the trader's real entry point: it sizes 10% of
        # balance and charges fee_pct on that notional.
        trader = BacktestTrader(initial_balance=10000, fee_pct=0.01, slippage_pct=0.0)
        signal = Signal(
            symbol='BTC/USDT', type=SignalType.BUY,
            timeframe='15m', conviction=Conviction.HIGH
        )
        trader.execute_signal(signal, price=100.0, timestamp=datetime(2023, 1, 1))
        # Notional = 10000 * 0.1 = 1000; fee = 1000 * 0.01 = 10 -> balance 9990.
        self.assertAlmostEqual(trader.balance, 9990.0)
        self.assertIn('BTC/USDT', trader.positions)
        self.assertEqual(trader.positions['BTC/USDT']['side'], 'BUY')


if __name__ == '__main__':
    unittest.main()
