import json
import os
import unittest

from execution.crypto_exits import CryptoExitTracker, default_exits_path
from unittest.mock import patch


class TestCryptoExitTracker(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_crypto_exits.json')
        self.addCleanup(lambda: os.path.exists(self.path) and os.remove(self.path))
        self.tracker = CryptoExitTracker(path=self.path)

    def _pos(self, symbol, price):
        return {'symbol': symbol, 'current_price': price}

    def test_take_profit_triggers_for_long(self):
        self.tracker.record('ETH/USD', 'BUY', stop_loss=1600, take_profit=1800)
        # Alpaca reports the symbol as ETHUSD (no slash) — must still match.
        hits = self.tracker.positions_to_close([self._pos('ETHUSD', 1850)])
        self.assertEqual(hits, [('ETHUSD', 'take_profit')])

    def test_stop_loss_triggers_for_long(self):
        self.tracker.record('BTC/USD', 'BUY', stop_loss=58000, take_profit=66000)
        hits = self.tracker.positions_to_close([self._pos('BTCUSD', 57000)])
        self.assertEqual(hits, [('BTCUSD', 'stop_loss')])

    def test_no_trigger_when_price_in_range(self):
        self.tracker.record('ETH/USD', 'BUY', stop_loss=1600, take_profit=1800)
        self.assertEqual(self.tracker.positions_to_close([self._pos('ETHUSD', 1700)]), [])

    def test_untracked_symbol_ignored(self):
        # A stock position (managed by Alpaca bracket) isn't tracked here.
        self.assertEqual(self.tracker.positions_to_close([self._pos('AAPL', 999)]), [])

    def test_discard_stops_tracking(self):
        self.tracker.record('ETH/USD', 'BUY', 1600, 1800)
        self.tracker.discard('ETHUSD')  # discard by normalised symbol
        self.assertEqual(self.tracker.positions_to_close([self._pos('ETHUSD', 1850)]), [])

    def test_persists_across_instances(self):
        self.tracker.record('ETH/USD', 'BUY', 1600, 1800)
        reloaded = CryptoExitTracker(path=self.path)
        hits = reloaded.positions_to_close([self._pos('ETHUSD', 1850)])
        self.assertEqual(hits, [('ETHUSD', 'take_profit')])

    def test_file_is_valid_json(self):
        self.tracker.record('ETH/USD', 'BUY', 1600, 1800)
        with open(self.path) as fh:
            data = json.load(fh)
        self.assertIn('ETHUSD', data)

    def test_default_path_env_override(self):
        with patch.dict(os.environ, {'MINUTETRADER_CRYPTO_EXITS_PATH': '/x/e.json'}):
            self.assertEqual(default_exits_path(), '/x/e.json')


if __name__ == '__main__':
    unittest.main()
