import json
import os
import unittest
from unittest.mock import patch

from execution.paper_trader import PaperTrader
from execution.reconciliation import (
    reconcile,
    reconcile_paper_trader,
    load_broker_snapshot,
    default_snapshot_path,
)


class TestReconcile(unittest.TestCase):
    def test_in_sync_when_positions_match(self):
        bot = {'BTC/USD': {'side': 'BUY', 'amount': 0.05}}
        broker = [{'symbol': 'BTC/USD', 'qty': 0.05}]
        result = reconcile(bot, broker)
        self.assertTrue(result['in_sync'])
        self.assertEqual(len(result['matched']), 1)

    def test_only_in_bot_flagged(self):
        bot = {'AAPL': {'side': 'BUY', 'amount': 10}}
        result = reconcile(bot, [])
        self.assertFalse(result['in_sync'])
        self.assertEqual(result['only_in_bot'][0]['symbol'], 'AAPL')

    def test_only_in_broker_flagged(self):
        broker = [{'symbol': 'TSLA', 'amount': 3, 'side': 'SELL'}]
        result = reconcile({}, broker)
        self.assertFalse(result['in_sync'])
        self.assertEqual(result['only_in_broker'][0]['symbol'], 'TSLA')
        self.assertEqual(result['only_in_broker'][0]['broker_qty'], -3.0)  # SELL -> negative

    def test_quantity_mismatch_flagged(self):
        bot = {'ETH/USD': {'side': 'BUY', 'amount': 2.0}}
        broker = [{'symbol': 'ETH/USD', 'qty': 1.5}]
        result = reconcile(bot, broker)
        self.assertFalse(result['in_sync'])
        m = result['quantity_mismatch'][0]
        self.assertEqual(m['bot_qty'], 2.0)
        self.assertEqual(m['broker_qty'], 1.5)

    def test_side_matters_buy_vs_sell(self):
        bot = {'AAPL': {'side': 'BUY', 'amount': 5}}
        broker = [{'symbol': 'AAPL', 'amount': 5, 'side': 'SELL'}]  # opposite direction
        result = reconcile(bot, broker)
        self.assertFalse(result['in_sync'])
        self.assertEqual(len(result['quantity_mismatch']), 1)

    def test_result_is_json_serializable(self):
        result = reconcile({'X': {'side': 'BUY', 'amount': 1}}, [{'symbol': 'Y', 'qty': 2}])
        json.dumps(result)


class TestSnapshotLoading(unittest.TestCase):
    def setUp(self):
        patcher = patch('execution.paper_trader.log_trade_attempt')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.trader = PaperTrader(10_000)
        self.path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_broker_snap.json')

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_missing_snapshot_returns_none(self):
        self.assertIsNone(load_broker_snapshot(self.path))
        self.assertIsNone(reconcile_paper_trader(self.trader, snapshot_path=self.path))

    def test_reconcile_paper_trader_from_file(self):
        self.trader.place_order('BTC/USD', 'BUY', 0.05, 60000.0)
        with open(self.path, 'w') as fh:
            json.dump({'positions': [{'symbol': 'BTC/USD', 'qty': 0.05}]}, fh)
        result = reconcile_paper_trader(self.trader, snapshot_path=self.path)
        self.assertIsNotNone(result)
        self.assertTrue(result['in_sync'])

    def test_bare_list_snapshot_accepted(self):
        with open(self.path, 'w') as fh:
            json.dump([{'symbol': 'AAPL', 'qty': 1}], fh)
        self.assertEqual(load_broker_snapshot(self.path), [{'symbol': 'AAPL', 'qty': 1}])

    def test_default_path_env_override(self):
        with patch.dict(os.environ, {'MINUTETRADER_BROKER_SNAPSHOT': '/x/snap.json'}):
            self.assertEqual(default_snapshot_path(), '/x/snap.json')


if __name__ == '__main__':
    unittest.main()
