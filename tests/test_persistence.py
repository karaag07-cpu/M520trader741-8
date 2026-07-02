import json
import os
import unittest
from unittest.mock import patch

from execution.paper_trader import PaperTrader, default_state_path


class TestPaperTraderPersistence(unittest.TestCase):
    def setUp(self):
        patcher = patch('execution.paper_trader.log_trade_attempt')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_paper_state.json')
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))

    def test_save_then_load_restores_balance_and_positions(self):
        t = PaperTrader(10_000)
        t.place_order('BTC/USD', 'BUY', 0.05, 60_000.0, stop_loss=58_000, take_profit=66_000)
        t.balance = 9_995.0
        t.save_state(self.path)

        fresh = PaperTrader(10_000)
        loaded = fresh.load_state(self.path)
        self.assertTrue(loaded)
        self.assertEqual(fresh.balance, 9_995.0)
        self.assertIn('BTC/USD', fresh.positions)
        self.assertEqual(fresh.positions['BTC/USD']['amount'], 0.05)

    def test_load_returns_false_when_no_file(self):
        fresh = PaperTrader(10_000)
        self.assertFalse(fresh.load_state(self.path))
        self.assertEqual(fresh.balance, 10_000)  # unchanged

    def test_saved_file_is_valid_json(self):
        t = PaperTrader(10_000)
        t.place_order('ETH/USD', 'SELL', 1.0, 3_000.0, stop_loss=3_100, take_profit=2_800)
        t.save_state(self.path)
        with open(self.path) as fh:
            data = json.load(fh)
        self.assertEqual(set(data.keys()), {'balance', 'positions', 'trade_history'})

    def test_committed_capital_consistent_after_reload(self):
        t = PaperTrader(10_000)
        t.place_order('BTC/USD', 'BUY', 0.1, 50_000.0)
        before = t.committed_capital()
        t.save_state(self.path)
        fresh = PaperTrader(10_000)
        fresh.load_state(self.path)
        self.assertAlmostEqual(fresh.committed_capital(), before)

    def test_default_state_path_env_override(self):
        with patch.dict(os.environ, {'MINUTETRADER_STATE_PATH': '/x/state.json'}):
            self.assertEqual(default_state_path(), '/x/state.json')


if __name__ == '__main__':
    unittest.main()
