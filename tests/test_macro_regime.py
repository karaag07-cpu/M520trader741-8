import unittest
import pandas as pd
from signals.macro_regime import MacroRegimeStrategy
from signals.base_strategy import Conviction, SignalType

class TestMacroRegime(unittest.TestCase):
    def setUp(self):
        self.strategy = MacroRegimeStrategy()

    def test_goldilocks(self):
        # YC > 0.5, INF < 3%
        signal = self.strategy.generate_signal(None, yc_spread=1.2, inflation_yoy=2.1, fed_rate_trend="Stable")
        self.assertEqual(signal.metadata['regime'], "Goldilocks")
        self.assertEqual(signal.metadata['global_bias'], "BULLISH")
        self.assertEqual(signal.metadata['position_size_modifier'], 1.0)
        self.assertEqual(signal.conviction, Conviction.HIGH)

    def test_deflationary_bust(self):
        # YC < 0
        signal = self.strategy.generate_signal(None, yc_spread=-0.2, inflation_yoy=-0.5, fed_rate_trend="Falling")
        self.assertEqual(signal.metadata['regime'], "Deflationary Bust")
        self.assertEqual(signal.metadata['global_bias'], "BEARISH")
        self.assertEqual(signal.metadata['position_size_modifier'], 0.0)

    def test_overheating(self):
        # INF > 4, FED Rising
        signal = self.strategy.generate_signal(None, yc_spread=0.3, inflation_yoy=4.5, fed_rate_trend="Rising")
        self.assertEqual(signal.metadata['regime'], "Overheating")
        self.assertEqual(signal.metadata['global_bias'], "NEUTRAL")
        self.assertEqual(signal.metadata['position_size_modifier'], 0.5)

if __name__ == "__main__":
    unittest.main()
