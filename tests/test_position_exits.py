import unittest
from unittest.mock import patch

from execution.paper_trader import PaperTrader


class TestPositionExits(unittest.TestCase):
    """Covers PaperTrader.update_positions, the exit path main.py drives.

    The main loop bug this guards against: exits were previously checked
    against a fresh random price draw instead of the real observed price.
    These tests pin the deterministic behaviour the fixed loop relies on --
    given a real price, stops/targets trigger only at the right thresholds.
    """

    def setUp(self):
        patcher = patch('execution.paper_trader.log_trade_attempt')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.trader = PaperTrader(initial_balance=10_000)

    def _open(self, side, entry, stop, take):
        self.trader.place_order('BTC/USDT', side, 1.0, entry,
                                stop_loss=stop, take_profit=take)

    def test_long_take_profit_triggers(self):
        self._open('BUY', entry=100.0, stop=95.0, take=110.0)
        self.trader.update_positions({'BTC/USDT': 111.0})
        self.assertNotIn('BTC/USDT', self.trader.positions)
        self.assertEqual(self.trader.trade_history[-1]['close_reason'], 'TAKE_PROFIT')

    def test_long_stop_loss_triggers(self):
        self._open('BUY', entry=100.0, stop=95.0, take=110.0)
        self.trader.update_positions({'BTC/USDT': 94.0})
        self.assertNotIn('BTC/USDT', self.trader.positions)
        self.assertEqual(self.trader.trade_history[-1]['close_reason'], 'STOP_LOSS')

    def test_price_in_range_keeps_position_open(self):
        self._open('BUY', entry=100.0, stop=95.0, take=110.0)
        self.trader.update_positions({'BTC/USDT': 102.0})
        self.assertIn('BTC/USDT', self.trader.positions)
        self.assertEqual(len(self.trader.trade_history), 0)

    def test_short_take_profit_triggers(self):
        self._open('SELL', entry=100.0, stop=105.0, take=90.0)
        self.trader.update_positions({'BTC/USDT': 89.0})
        self.assertNotIn('BTC/USDT', self.trader.positions)
        self.assertEqual(self.trader.trade_history[-1]['close_reason'], 'TAKE_PROFIT')

    def test_missing_price_leaves_position_untouched(self):
        # A symbol absent from the price dict must not close the position.
        self._open('BUY', entry=100.0, stop=95.0, take=110.0)
        self.trader.update_positions({'ETH/USDT': 50.0})
        self.assertIn('BTC/USDT', self.trader.positions)


if __name__ == '__main__':
    unittest.main()
