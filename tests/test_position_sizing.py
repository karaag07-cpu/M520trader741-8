import unittest
from risk.risk_manager import RiskManager


class TestPositionSizing(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(risk_reward_ratio=3.0)

    def test_fixed_fractional_quantity(self):
        # Risk 1% of 10,000 = 100. Stop distance = 100 - 95 = 5.
        # Quantity = 100 / 5 = 20 units.
        result = self.rm.validate_risk(
            account_balance=10_000, entry_price=100, stop_loss=95,
            risk_per_trade=0.01, max_position_fraction=1.0
        )
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['quantity'], 20.0)
        self.assertAlmostEqual(result['risk_amount'], 100.0)
        self.assertAlmostEqual(result['stop_distance'], 5.0)

    def test_notional_cap_enforced(self):
        # A very tight stop would size huge; the 10% notional cap must bind.
        result = self.rm.validate_risk(
            account_balance=10_000, entry_price=100, stop_loss=99.99,
            risk_per_trade=0.02, max_position_fraction=0.10
        )
        self.assertIsNotNone(result)
        self.assertLessEqual(result['notional'], 10_000 * 0.10 + 1e-6)

    def test_size_modifier_scales_risk(self):
        full = self.rm.validate_risk(10_000, 100, 95, risk_per_trade=0.01,
                                     max_position_fraction=1.0, size_modifier=1.0)
        half = self.rm.validate_risk(10_000, 100, 95, risk_per_trade=0.01,
                                     max_position_fraction=1.0, size_modifier=0.5)
        self.assertAlmostEqual(half['quantity'], full['quantity'] * 0.5)

    def test_zero_modifier_stands_aside(self):
        # A risk-off macro regime (modifier 0.0) should produce no position.
        result = self.rm.validate_risk(10_000, 100, 95, size_modifier=0.0)
        self.assertIsNone(result)

    def test_invalid_inputs_return_none(self):
        self.assertIsNone(self.rm.validate_risk(0, 100, 95))          # no balance
        self.assertIsNone(self.rm.validate_risk(10_000, 0, 95))       # bad price
        self.assertIsNone(self.rm.validate_risk(10_000, 100, 100))    # zero stop distance
        self.assertIsNone(self.rm.validate_risk(10_000, 100, 95, risk_per_trade=1.5))

    def test_integration_with_trade_levels(self):
        # Derive the stop from calculate_trade_levels, then size off it.
        levels = self.rm.calculate_trade_levels("BUY", 145, atr=10.0, atr_multiplier=2.0)
        result = self.rm.validate_risk(
            account_balance=50_000, entry_price=145, stop_loss=levels['stop_loss'],
            risk_per_trade=0.01, max_position_fraction=1.0
        )
        self.assertIsNotNone(result)
        # stop_distance = 145 - 125 = 20; risk = 500; qty = 25.
        self.assertAlmostEqual(result['quantity'], 25.0)


if __name__ == '__main__':
    unittest.main()
