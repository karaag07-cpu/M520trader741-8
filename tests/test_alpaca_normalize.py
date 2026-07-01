import unittest
import pandas as pd

from data.fetchers import normalize_alpaca_bars


def _alpaca_like_df(symbol='AAPL', n=3):
    """Mimic Alpaca's BarSet.df: MultiIndex (symbol, timestamp) + extra cols."""
    ts = pd.date_range('2024-01-01', periods=n, freq='15min')
    idx = pd.MultiIndex.from_product([[symbol], ts], names=['symbol', 'timestamp'])
    return pd.DataFrame({
        'open': [100.0 + i for i in range(n)],
        'high': [101.0 + i for i in range(n)],
        'low': [99.0 + i for i in range(n)],
        'close': [100.5 + i for i in range(n)],
        'volume': [1000 + i for i in range(n)],
        'trade_count': [10] * n,
        'vwap': [100.2 + i for i in range(n)],
    }, index=idx)


class TestNormalizeAlpacaBars(unittest.TestCase):
    def test_flattens_to_standard_ohlcv_columns(self):
        out = normalize_alpaca_bars(_alpaca_like_df('AAPL', 3), 'AAPL')
        self.assertEqual(list(out.columns), ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(len(out), 3)
        self.assertNotIn('vwap', out.columns)
        self.assertNotIn('trade_count', out.columns)

    def test_sets_symbol_attr(self):
        out = normalize_alpaca_bars(_alpaca_like_df('TSLA', 2), 'TSLA')
        self.assertEqual(out.attrs['symbol'], 'TSLA')

    def test_values_preserved(self):
        out = normalize_alpaca_bars(_alpaca_like_df('AAPL', 3), 'AAPL')
        self.assertAlmostEqual(out['close'].iloc[-1], 102.5)
        self.assertAlmostEqual(out['open'].iloc[0], 100.0)

    def test_empty_input_returns_wellformed_empty_frame(self):
        out = normalize_alpaca_bars(pd.DataFrame(), 'AAPL')
        self.assertEqual(list(out.columns), ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(len(out), 0)
        self.assertEqual(out.attrs['symbol'], 'AAPL')

    def test_output_feeds_indicators(self):
        # The normalised frame should be consumable by the indicator layer.
        from data.processors import calculate_atr
        out = normalize_alpaca_bars(_alpaca_like_df('AAPL', 20), 'AAPL')
        atr = calculate_atr(out, period=14)
        self.assertIsNotNone(atr)
        self.assertGreater(atr, 0)


if __name__ == '__main__':
    unittest.main()
