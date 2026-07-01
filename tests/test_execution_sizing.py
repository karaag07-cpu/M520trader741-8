import unittest
from unittest.mock import patch

from risk.risk_manager import RiskManager
from execution.paper_trader import PaperTrader


class TestExecutionSizing(unittest.TestCase):
    """Verifies the main.py wiring: trade levels -> validate_risk -> place_order.

    Rather than driving main()'s infinite loop, this exercises the exact
    object interactions main.py now performs, so the risk-sized quantity is
    what actually reaches the paper trader.
    """

    def setUp(self):
        self.rm = RiskManager(risk_reward_ratio=3.0)
        # The paper trader logs to an external `team-db` CLI; stub it so the
        # test is hermetic and doesn't depend on that binary being present.
        patcher = patch('execution.paper_trader.log_trade_attempt')
        self.mock_log = patcher.start()
        self.addCleanup(patcher.stop)
        self.trader = PaperTrader(initial_balance=10_000)

    def _place_from_signal(self, side, current_price, atr=10.0,
                           risk_per_trade=0.01, size_modifier=1.0):
        """Mirror main.py's risk + execution path for one signal."""
        levels = self.rm.calculate_trade_levels(side, current_price, atr=atr)
        entry_price = (levels['entry_zone'][0] + levels['entry_zone'][1]) / 2
        sizing = self.rm.validate_risk(
            account_balance=self.trader.balance,
            entry_price=entry_price,
            stop_loss=levels['stop_loss'],
            risk_per_trade=risk_per_trade,
            max_position_fraction=0.25,
            size_modifier=size_modifier,
        )
        if not sizing:
            return None, sizing
        trade = self.trader.place_order(
            "BTC/USDT", side, sizing['quantity'], entry_price,
            stop_loss=levels['stop_loss'], take_profit=levels['tp_levels'][0],
        )
        return trade, sizing

    def test_risk_sized_quantity_reaches_paper_trader(self):
        trade, sizing = self._place_from_signal("BUY", current_price=100.0, atr=1.0)
        self.assertIsNotNone(trade)
        # The order amount is exactly the quantity the risk manager computed.
        self.assertAlmostEqual(trade['amount'], sizing['quantity'])
        # And the risk taken never exceeds the 1% budget on 10k = 100.
        self.assertLessEqual(sizing['risk_amount'], 100.0 + 1e-6)
        self.assertEqual(self.trader.positions['BTC/USDT']['side'], 'BUY')

    def test_macro_modifier_scales_executed_size(self):
        # Wide stop (atr=5) keeps sizing below the notional cap so the
        # modifier's scaling is visible rather than clipped.
        _, full = self._place_from_signal("BUY", 100.0, atr=5.0, size_modifier=1.0)
        self.trader.positions.clear()
        _, half = self._place_from_signal("BUY", 100.0, atr=5.0, size_modifier=0.5)
        self.assertAlmostEqual(half['quantity'], full['quantity'] * 0.5)

    def test_notional_never_exceeds_balance(self):
        # Even an aggressive risk fraction stays within the paper trader's cash
        # (validate_risk's notional cap keeps place_order from rejecting).
        trade, sizing = self._place_from_signal(
            "BUY", 100.0, atr=0.01, risk_per_trade=0.5
        )
        self.assertIsNotNone(trade)
        self.assertLessEqual(sizing['notional'], self.trader.balance)

    def test_sell_side_records_short(self):
        trade, _ = self._place_from_signal("SELL", current_price=200.0, atr=2.0)
        self.assertIsNotNone(trade)
        self.assertEqual(trade['side'], 'SELL')
        # Stop is above entry for a short.
        self.assertGreater(trade['stop_loss'], trade['entry_price'])


if __name__ == '__main__':
    unittest.main()
