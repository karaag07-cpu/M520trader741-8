import unittest
import pandas as pd
from data.processors import calculate_atr, latest_atr
from risk.risk_manager import RiskManager


def _flat_range_df(n=20, high=101.0, low=99.0, close=100.0):
    """Bars with a constant 2.0 true range -> ATR converges to 2.0."""
    return pd.DataFrame({
        'open': [close] * n,
        'high': [high] * n,
        'low': [low] * n,
        'close': [close] * n,
        'volume': [1000.0] * n,
    })


class TestATR(unittest.TestCase):
    def test_atr_constant_range(self):
        atr = latest_atr(_flat_range_df(20), period=14)
        self.assertAlmostEqual(atr, 2.0, places=6)

    def test_atr_insufficient_data_returns_none(self):
        self.assertIsNone(latest_atr(_flat_range_df(5), period=14))
        self.assertIsNone(latest_atr(None, period=14))

    def test_atr_series_early_values_nan(self):
        atr = calculate_atr(_flat_range_df(20), period=14)
        self.assertTrue(pd.isna(atr.iloc[0]))
        self.assertAlmostEqual(atr.iloc[-1], 2.0, places=6)


class TestVolatilityScaledLevels(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(risk_reward_ratio=3.0)

    def test_atr_stop_and_targets(self):
        levels = self.rm.calculate_trade_levels("BUY", 100.0, atr=2.0, atr_stop_mult=2.0)
        # stop distance = 2 * 2 = 4 -> stop at 96; tp distance = rr(3)*4 = 12
        self.assertAlmostEqual(levels['stop_loss'], 96.0)
        self.assertAlmostEqual(levels['tp_levels'][0], 112.0)
        self.assertAlmostEqual(levels['tp_levels'][1], 118.0)
        self.assertAlmostEqual(levels['tp_levels'][2], 124.0)

    def test_sell_side_atr(self):
        levels = self.rm.calculate_trade_levels("SELL", 100.0, atr=2.0, atr_stop_mult=2.0)
        self.assertAlmostEqual(levels['stop_loss'], 104.0)
        self.assertAlmostEqual(levels['tp_levels'][0], 88.0)

    def test_fallback_matches_flat_percentage(self):
        # atr=None must reproduce the original flat-1% behaviour exactly.
        levels = self.rm.calculate_trade_levels("BUY", 100.0)
        self.assertAlmostEqual(levels['stop_loss'], 99.0)
        self.assertAlmostEqual(levels['tp_levels'][0], 103.0)
        self.assertAlmostEqual(levels['tp_levels'][1], 104.5)
        self.assertAlmostEqual(levels['tp_levels'][2], 106.0)

    def test_higher_volatility_yields_smaller_size(self):
        # Same account/entry: a more volatile asset gets a wider stop and thus
        # a smaller position, equalising dollar risk.
        low_vol = self.rm.calculate_trade_levels("BUY", 100.0, atr=0.5, atr_stop_mult=2.0)
        high_vol = self.rm.calculate_trade_levels("BUY", 100.0, atr=2.0, atr_stop_mult=2.0)

        size_low = self.rm.calculate_position_size(10000, 100.0, low_vol['stop_loss'])
        size_high = self.rm.calculate_position_size(10000, 100.0, high_vol['stop_loss'])

        self.assertGreater(size_low, size_high)
        # Dollar risk at stop should be ~equal (= balance * risk_per_trade = 100)
        self.assertAlmostEqual(size_low * (100.0 - low_vol['stop_loss']), 100.0, places=6)
        self.assertAlmostEqual(size_high * (100.0 - high_vol['stop_loss']), 100.0, places=6)


if __name__ == '__main__':
    unittest.main()
