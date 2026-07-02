import unittest
from unittest.mock import MagicMock, patch

from execution.alpaca_broker import AlpacaBroker, _order_params


class TestOrderParams(unittest.TestCase):
    def test_equity_uses_day_order(self):
        p = _order_params('AAPL', 'BUY', 3)
        self.assertEqual(p['time_in_force'], 'day')
        self.assertEqual(p['side'], 'BUY')
        self.assertEqual(p['qty'], 3.0)

    def test_crypto_uses_gtc(self):
        p = _order_params('BTC/USD', 'sell', 0.05)
        self.assertEqual(p['time_in_force'], 'gtc')
        self.assertEqual(p['side'], 'SELL')

    def test_side_normalised(self):
        self.assertEqual(_order_params('AAPL', 'buy', 1)['side'], 'BUY')
        self.assertEqual(_order_params('AAPL', 'SELL', 1)['side'], 'SELL')


class TestAlpacaBroker(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.broker = AlpacaBroker(client=self.client)  # inject fake client (no SDK)

    def test_submit_order_calls_client(self):
        # Patch the SDK-dependent request builder so no alpaca import is needed.
        with patch.object(self.broker, '_build_order_request', return_value='REQ') as build:
            self.broker.submit_order('AAPL', 'BUY', 2.0)
        build.assert_called_once_with('AAPL', 'BUY', 2.0)
        self.client.submit_order.assert_called_once_with('REQ')

    def test_get_positions_maps_and_signs(self):
        long_pos = MagicMock(symbol='AAPL', qty='10')
        short_pos = MagicMock(symbol='TSLA', qty='-3')
        self.client.get_all_positions.return_value = [long_pos, short_pos]
        positions = self.broker.get_positions()
        self.assertEqual(positions[0], {'symbol': 'AAPL', 'qty': 10.0, 'side': 'BUY'})
        self.assertEqual(positions[1], {'symbol': 'TSLA', 'qty': -3.0, 'side': 'SELL'})

    def test_get_account_extracts_fields(self):
        self.client.get_account.return_value = MagicMock(status='ACTIVE', cash='99998.76', buying_power='399995.04')
        acct = self.broker.get_account()
        self.assertEqual(acct['status'], 'ACTIVE')
        self.assertAlmostEqual(acct['cash'], 99998.76)
        self.assertAlmostEqual(acct['buying_power'], 399995.04)

    def test_positions_feed_reconciliation(self):
        # The broker's position shape must be consumable by reconcile().
        from execution.reconciliation import reconcile
        self.client.get_all_positions.return_value = [MagicMock(symbol='BTC/USD', qty='0.05')]
        bot = {'BTC/USD': {'side': 'BUY', 'amount': 0.05}}
        result = reconcile(bot, self.broker.get_positions())
        self.assertTrue(result['in_sync'])


if __name__ == '__main__':
    unittest.main()
