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

    def test_submit_order_passes_brackets_to_builder(self):
        # Patch the SDK-dependent request builder so no alpaca import is needed.
        with patch.object(self.broker, '_build_order_request', return_value='REQ') as build:
            self.broker.submit_order('AAPL', 'BUY', 2.0, take_profit=110.0, stop_loss=95.0)
        build.assert_called_once_with('AAPL', 'BUY', 2.0, 110.0, 95.0)
        self.client.submit_order.assert_called_once_with('REQ')

    def test_get_positions_maps_signs_and_prices(self):
        long_pos = MagicMock(symbol='AAPL', qty='10', avg_entry_price='100', current_price='105', unrealized_pl='50')
        short_pos = MagicMock(symbol='TSLA', qty='-3', avg_entry_price='200', current_price='198', unrealized_pl='6')
        self.client.get_all_positions.return_value = [long_pos, short_pos]
        positions = self.broker.get_positions()
        self.assertEqual(positions[0]['side'], 'BUY')
        self.assertEqual(positions[0]['qty'], 10.0)
        self.assertAlmostEqual(positions[0]['current_price'], 105.0)
        self.assertAlmostEqual(positions[0]['unrealized_pnl'], 50.0)
        self.assertEqual(positions[1]['side'], 'SELL')

    def test_get_account_extracts_fields(self):
        self.client.get_account.return_value = MagicMock(
            status='ACTIVE', cash='99998.76', buying_power='399995.04',
            equity='100050.0', portfolio_value='100050.0')
        acct = self.broker.get_account()
        self.assertIn('ACTIVE', acct['status'])
        self.assertAlmostEqual(acct['cash'], 99998.76)
        self.assertAlmostEqual(acct['equity'], 100050.0)

    def test_positions_feed_reconciliation(self):
        # The broker's position shape must be consumable by reconcile().
        from execution.reconciliation import reconcile
        self.client.get_all_positions.return_value = [
            MagicMock(symbol='BTC/USD', qty='0.05', avg_entry_price='60000', current_price='61000', unrealized_pl='50')
        ]
        bot = {'BTC/USD': {'side': 'BUY', 'amount': 0.05}}
        result = reconcile(bot, self.broker.get_positions())
        self.assertTrue(result['in_sync'])


class TestBuildAlpacaStatus(unittest.TestCase):
    def test_maps_account_and_positions_to_dashboard_shape(self):
        from execution.status_reporter import build_alpaca_status
        account = {'cash': 99998.76, 'buying_power': 399995.0, 'equity': 100050.0,
                   'portfolio_value': 100050.0, 'status': 'ACTIVE'}
        positions = [
            {'symbol': 'AAPL', 'qty': 10.0, 'side': 'BUY', 'entry_price': 100.0,
             'current_price': 105.0, 'unrealized_pnl': 50.0},
        ]
        status = build_alpaca_status(account, positions, regime={'regime': 'Goldilocks'})
        self.assertEqual(status['source'], 'alpaca')
        self.assertAlmostEqual(status['balance'], 99998.76)
        self.assertAlmostEqual(status['portfolio_value'], 100050.0)
        self.assertEqual(status['open_position_count'], 1)
        self.assertAlmostEqual(status['committed_capital'], 1000.0)  # 10 * 100
        self.assertEqual(status['open_positions'][0]['symbol'], 'AAPL')
        self.assertEqual(status['regime']['regime'], 'Goldilocks')

    def test_empty_account(self):
        from execution.status_reporter import build_alpaca_status
        status = build_alpaca_status({'cash': 100.0, 'equity': 100.0}, [])
        self.assertEqual(status['open_position_count'], 0)
        self.assertEqual(status['committed_capital'], 0.0)


if __name__ == '__main__':
    unittest.main()
