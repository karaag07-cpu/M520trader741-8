import unittest
import math
import pandas as pd

from data.processors import calculate_atr, atr_series


class TestATR(unittest.TestCase):
    def _constant_tr_frame(self, n=30, close=100.0, half_range=5.0):
        # high-low = 2*half_range every bar, and closes are flat so the
        # gap-based true-range terms never exceed it -> TR is constant.
        return pd.DataFrame({
            'high': [close + half_range] * n,
            'low': [close - half_range] * n,
            'close': [close] * n,
        })

    def test_none_when_insufficient_data(self):
        df = self._constant_tr_frame(n=3)
        self.assertIsNone(calculate_atr(df, period=14))

    def test_constant_true_range_converges_to_that_range(self):
        # TR == 10 on every bar, so Wilder's ATR must be exactly 10.
        df = self._constant_tr_frame(n=30, half_range=5.0)  # range = 10
        self.assertAlmostEqual(calculate_atr(df, period=14), 10.0, places=6)

    def test_returns_native_float(self):
        df = self._constant_tr_frame(n=30)
        self.assertIsInstance(calculate_atr(df, period=14), float)

    def test_series_nan_before_period_then_defined(self):
        df = self._constant_tr_frame(n=30)
        s = atr_series(df, period=14)
        self.assertEqual(len(s), len(df))
        self.assertTrue(math.isnan(s.iloc[12]))   # before period-1
        self.assertFalse(math.isnan(s.iloc[-1]))  # defined at the end

    def test_wilder_differs_from_simple_mean_after_a_spike(self):
        # Build steady TR then one big spike; Wilder's smoothing should carry
        # more of the spike forward than a flat rolling mean would once the
        # spike ages out of a simple window.
        n = 40
        highs = [105.0] * n
        lows = [95.0] * n
        closes = [100.0] * n
        highs[20] = 200.0  # a volatility spike on bar 20
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        wilder = calculate_atr(df, period=14)
        simple = pd.concat([
            (df['high'] - df['low']),
            (df['high'] - df['close'].shift(1)).abs(),
            (df['low'] - df['close'].shift(1)).abs(),
        ], axis=1).max(axis=1).rolling(14).mean().iloc[-1]
        # The spike is >14 bars back, so the simple mean has fully forgotten it
        # (back to 10), while Wilder's retains a residual above 10.
        self.assertAlmostEqual(simple, 10.0, places=6)
        self.assertGreater(wilder, 10.0)


if __name__ == '__main__':
    unittest.main()
