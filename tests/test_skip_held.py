import logging
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import main
from main import TradingBot, _norm_symbol
from signals.base_strategy import Signal, SignalType, Conviction


def _quiet_logger():
    lg = logging.getLogger('minutetrader.skiptest')
    lg.addHandler(logging.NullHandler())
    lg.propagate = False
    return lg


class _FakeBroker:
    def __init__(self, positions):
        self._positions = positions
        self.submit_order = MagicMock()
        self.close_position = MagicMock()

    def get_account(self):
        return {'equity': 100000.0, 'cash': 100000.0, 'buying_power': 400000.0,
                'portfolio_value': 100000.0, 'status': 'ACTIVE'}

    def get_positions(self):
        return self._positions

    def get_portfolio_history(self, *a, **k):
        return []


class TestNormSymbol(unittest.TestCase):
    def test_crypto_formats_match(self):
        self.assertEqual(_norm_symbol('BTC/USD'), _norm_symbol('BTCUSD'))
        self.assertEqual(_norm_symbol('BTC/USD'), 'BTCUSD')

    def test_equity_unchanged(self):
        self.assertEqual(_norm_symbol('AAPL'), 'AAPL')


class TestSkipHeldCrypto(unittest.TestCase):
    def setUp(self):
        for p in (patch('main.write_status', lambda *a, **k: None),
                  patch('execution.paper_trader.log_trade_attempt')):
            p.start()
        self.addCleanup(patch.stopall)
        self._ce = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_skip_ce.json')
        self.addCleanup(lambda: os.path.exists(self._ce) and os.remove(self._ce))

        self.bot = TradingBot(config={}, logger=_quiet_logger())
        # Inject an Alpaca broker already holding BTC (reported as 'BTCUSD').
        self.bot.broker = _FakeBroker([{
            'symbol': 'BTCUSD', 'qty': 0.5, 'side': 'BUY',
            'entry_price': 60000.0, 'current_price': 61000.0, 'unrealized_pnl': 500.0,
        }])
        self.bot.crypto_exits = main.CryptoExitTracker(path=self._ce)
        self.bot._crypto_symbols = {'BTCUSD', 'ETHUSD', 'SOLUSD'}

    def test_held_crypto_is_not_rebought(self):
        # Force a fresh BUY signal on BTC/USD every symbol it's asked about.
        def fake_combine(signals, symbol):
            if symbol == 'BTC/USD':
                return Signal(symbol='BTC/USD', type=SignalType.BUY,
                              timeframe='15m', conviction=Conviction.HIGH)
            return None

        with patch.object(self.bot.combiner, 'combine', side_effect=fake_combine), \
             patch('main.now_eastern', return_value=datetime(2026, 7, 8, 12, 0)):
            self.bot.run_cycle()

        # BTC is already held (BTCUSD == BTC/USD after normalisation) -> no new order.
        self.bot.broker.submit_order.assert_not_called()


if __name__ == '__main__':
    unittest.main()
