import logging
import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import main
from main import TradingBot
from signals.base_strategy import Signal, SignalType, Conviction


def _quiet_logger():
    lg = logging.getLogger('minutetrader.wholeshares')
    lg.addHandler(logging.NullHandler())
    lg.propagate = False
    return lg


class _FakeBroker:
    def __init__(self):
        self.submit_order = MagicMock()
        self.close_position = MagicMock()

    def get_account(self):
        return {'equity': 93000.0, 'cash': 93000.0, 'buying_power': 300000.0,
                'portfolio_value': 93000.0, 'status': 'ACTIVE'}

    def get_positions(self):
        return []


class TestWholeShareRounding(unittest.TestCase):
    def setUp(self):
        for p in (patch('main.write_status', lambda *a, **k: None),
                  patch('execution.paper_trader.log_trade_attempt')):
            p.start()
        self.addCleanup(patch.stopall)
        self._ce = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'mt_ws_ce.json')
        self.addCleanup(lambda: os.path.exists(self._ce) and os.remove(self._ce))
        self.bot = TradingBot(config={}, logger=_quiet_logger())
        self.bot.broker = _FakeBroker()
        self.bot.crypto_exits = main.CryptoExitTracker(path=self._ce)
        self.bot._crypto_symbols = {'BTCUSD', 'ETHUSD', 'SOLUSD'}

    def test_equity_order_qty_is_whole_shares(self):
        def fake_combine(signals, symbol):
            if symbol == 'AAPL':
                return Signal(symbol='AAPL', type=SignalType.BUY,
                              timeframe='15m', conviction=Conviction.HIGH)
            return None

        # Midday on a weekday (2026-07-15 is a Wednesday) -> equity market open.
        with patch.object(self.bot.combiner, 'combine', side_effect=fake_combine), \
             patch('main.now_eastern', return_value=datetime(2026, 7, 15, 12, 0)):
            self.bot.run_cycle()

        self.bot.broker.submit_order.assert_called()
        qty = self.bot.broker.submit_order.call_args.args[2]
        self.assertEqual(qty, float(int(qty)))   # whole shares
        self.assertGreaterEqual(qty, 1)


if __name__ == '__main__':
    unittest.main()
