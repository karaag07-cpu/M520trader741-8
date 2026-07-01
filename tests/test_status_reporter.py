import json
import os
import unittest
from unittest.mock import patch

from execution.paper_trader import PaperTrader
from execution.status_reporter import build_status, write_status, default_status_path


class TestStatusReporter(unittest.TestCase):
    def setUp(self):
        patcher = patch('execution.paper_trader.log_trade_attempt')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.trader = PaperTrader(initial_balance=10_000)

    def test_build_status_reports_flat_account(self):
        status = build_status(self.trader, prices={})
        self.assertEqual(status['balance'], 10_000)
        self.assertEqual(status['open_position_count'], 0)
        self.assertEqual(status['committed_capital'], 0)
        self.assertEqual(status['available_buying_power'], 10_000)
        self.assertIn('updated_at', status)

    def test_build_status_includes_open_position_and_unrealized_pnl(self):
        self.trader.place_order('BTC/USD', 'BUY', 2.0, 100.0,
                                stop_loss=95.0, take_profit=110.0)
        status = build_status(self.trader, prices={'BTC/USD': 105.0}, regime={'regime': 'Goldilocks'})
        self.assertEqual(status['open_position_count'], 1)
        pos = status['open_positions'][0]
        self.assertEqual(pos['symbol'], 'BTC/USD')
        self.assertEqual(pos['current_price'], 105.0)
        self.assertAlmostEqual(pos['unrealized_pnl'], (105.0 - 100.0) * 2.0)
        self.assertEqual(status['regime']['regime'], 'Goldilocks')

    def test_build_status_is_json_serializable(self):
        self.trader.place_order('ETH/USD', 'BUY', 1.0, 50.0, stop_loss=48, take_profit=55)
        status = build_status(self.trader, prices={'ETH/USD': 51.0})
        json.dumps(status)  # must not raise

    def test_write_status_roundtrip(self):
        target = os.path.join(
            os.environ.get('TMPDIR', '/tmp'), 'mt_status_test', 'status.json'
        )
        status = build_status(self.trader, prices={})
        written = write_status(status, path=target)
        self.assertEqual(written, target)
        with open(target) as fh:
            loaded = json.load(fh)
        self.assertEqual(loaded['balance'], 10_000)
        os.remove(target)

    def test_default_status_path_env_override(self):
        with patch.dict(os.environ, {'MINUTETRADER_STATUS_PATH': '/x/y/s.json'}):
            self.assertEqual(default_status_path(), '/x/y/s.json')

    def test_default_status_path_points_at_website(self):
        with patch.dict(os.environ, {}, clear=True):
            path = default_status_path()
        self.assertTrue(path.endswith(os.path.join('website', 'status.json')))


if __name__ == '__main__':
    unittest.main()
