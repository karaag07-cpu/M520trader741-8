import unittest
from unittest.mock import patch

from execution.paper_trader import PaperTrader


class TestBuyingPower(unittest.TestCase):
    """Concurrent positions must not collectively exceed available capital."""

    def setUp(self):
        patcher = patch('execution.paper_trader.log_trade_attempt')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.trader = PaperTrader(initial_balance=10_000)

    def test_committed_and_available_track_open_positions(self):
        self.assertEqual(self.trader.available_buying_power(), 10_000)
        self.trader.place_order('BTC/USDT', 'BUY', 1.0, 6_000.0)
        self.assertAlmostEqual(self.trader.committed_capital(), 6_000.0)
        self.assertAlmostEqual(self.trader.available_buying_power(), 4_000.0)

    def test_second_order_exceeding_remaining_capital_is_rejected(self):
        first = self.trader.place_order('BTC/USDT', 'BUY', 1.0, 7_000.0)
        self.assertIsNotNone(first)
        # Only 3,000 buying power left; a 5,000 order must be rejected.
        second = self.trader.place_order('ETH/USDT', 'BUY', 1.0, 5_000.0)
        self.assertIsNone(second)
        self.assertNotIn('ETH/USDT', self.trader.positions)

    def test_second_order_within_remaining_capital_succeeds(self):
        self.trader.place_order('BTC/USDT', 'BUY', 1.0, 7_000.0)
        second = self.trader.place_order('ETH/USDT', 'BUY', 1.0, 2_500.0)
        self.assertIsNotNone(second)
        self.assertIn('ETH/USDT', self.trader.positions)
        self.assertAlmostEqual(self.trader.available_buying_power(), 500.0)

    def test_total_notional_never_exceeds_capital_across_many_symbols(self):
        # Try to open five 2,500-notional positions on 10,000 of capital.
        placed = 0
        for i in range(5):
            if self.trader.place_order(f'SYM{i}/USDT', 'BUY', 1.0, 2_500.0):
                placed += 1
        # At most four fit (4 * 2,500 = 10,000); the fifth is rejected.
        self.assertEqual(placed, 4)
        self.assertLessEqual(self.trader.committed_capital(), 10_000 + 1e-6)

    def test_capital_frees_up_after_close(self):
        self.trader.place_order('BTC/USDT', 'BUY', 1.0, 9_000.0,
                                stop_loss=8_000.0, take_profit=10_000.0)
        # Hit take-profit to close it.
        self.trader.update_positions({'BTC/USDT': 10_001.0})
        self.assertNotIn('BTC/USDT', self.trader.positions)
        # Committed capital is released; full (plus PnL) buying power is back.
        self.assertEqual(self.trader.committed_capital(), 0.0)
        self.assertGreater(self.trader.available_buying_power(), 9_000.0)

    def test_reopening_same_symbol_not_falsely_blocked(self):
        # A symbol's own existing notional shouldn't count against replacing it.
        self.trader.place_order('BTC/USDT', 'BUY', 1.0, 9_000.0)
        replacement = self.trader.place_order('BTC/USDT', 'BUY', 1.0, 9_500.0)
        self.assertIsNotNone(replacement)
        self.assertAlmostEqual(self.trader.positions['BTC/USDT']['entry_price'], 9_500.0)


if __name__ == '__main__':
    unittest.main()
