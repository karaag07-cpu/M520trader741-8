import unittest
import pandas as pd
import numpy as np
from data.processors import calculate_atr
from risk.risk_manager import RiskManager

class TestRiskATR(unittest.TestCase):
    def setUp(self):
        # Create a mock dataframe
        data = {
            'high': [110, 112, 115, 118, 120, 122, 125, 128, 130, 132, 135, 138, 140, 145, 150],
            'low':  [100, 102, 105, 108, 110, 112, 115, 118, 120, 122, 125, 128, 130, 135, 140],
            'close': [105, 108, 110, 112, 115, 118, 120, 122, 125, 128, 130, 132, 135, 140, 145]
        }
        self.df = pd.DataFrame(data)
        self.rm = RiskManager(risk_reward_ratio=3.0)

    def test_calculate_atr(self):
        atr = calculate_atr(self.df, period=5)
        self.assertIsNotNone(atr)
        self.assertIsInstance(atr, float)
        # TRs: 
        # 1: 112-102=10, 112-105=7, 102-105=3 -> 10
        # 2: 115-105=10, 115-108=7, 105-108=3 -> 10
        # ... it's consistently around 10 in this mock data
        self.assertGreater(atr, 0)

    def test_calculate_trade_levels_with_atr(self):
        current_price = 145
        atr = 10.0
        multiplier = 2.0
        
        # BUY
        levels = self.rm.calculate_trade_levels("BUY", current_price, atr=atr, atr_multiplier=multiplier)
        # stop_distance = 10 * 2 = 20
        # stop_loss = 145 - 20 = 125
        # tp_distance = 20 * 3 = 60
        # tp1 = 145 + 60 = 205
        
        self.assertEqual(levels['stop_loss'], 125)
        self.assertEqual(levels['tp_levels'][0], 205)
        
        # SELL
        levels = self.rm.calculate_trade_levels("SELL", current_price, atr=atr, atr_multiplier=multiplier)
        # stop_loss = 145 + 20 = 165
        # tp1 = 145 - 60 = 85
        self.assertEqual(levels['stop_loss'], 165)
        self.assertEqual(levels['tp_levels'][0], 85)

    def test_calculate_trade_levels_fallback(self):
        current_price = 100.0
        # BUY fallback (1% stop)
        levels = self.rm.calculate_trade_levels("BUY", current_price)
        # stop_distance = 100 * 0.01 = 1.0
        # stop_loss = 100 - 1 = 99.0
        # tp_distance = 1 * 3 = 3.0
        # tp1 = 100 + 3 = 103.0
        
        self.assertEqual(levels['stop_loss'], 99.0)
        self.assertEqual(levels['tp_levels'][0], 103.0)

if __name__ == '__main__':
    unittest.main()
