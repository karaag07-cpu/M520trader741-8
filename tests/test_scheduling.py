import logging
import os
import unittest
from unittest.mock import patch

import main as main_mod
from main import TradingBot, build_parser


def _quiet_logger():
    lg = logging.getLogger('minutetrader.test')
    lg.addHandler(logging.NullHandler())
    lg.propagate = False
    return lg


class TestScheduling(unittest.TestCase):
    def setUp(self):
        # Empty config -> no live fetchers -> mock-data fallback (no network).
        # Patch side effects: status file write + the paper trader's DB logger.
        self._patchers = [
            patch('main.write_status', lambda *a, **k: None),
            patch('execution.paper_trader.log_trade_attempt'),
        ]
        for p in self._patchers:
            p.start()
            self.addCleanup(p.stop)
        self.bot = TradingBot(config={}, logger=_quiet_logger())

    def test_run_cycle_returns_status_snapshot(self):
        status = self.bot.run_cycle()
        self.assertIsNotNone(status)
        self.assertIn('balance', status)
        self.assertIn('open_positions', status)
        self.assertIn('portfolio_value', status)

    def test_run_once_executes_a_single_cycle(self):
        with patch.object(self.bot, 'run_cycle', wraps=self.bot.run_cycle) as spy:
            count = self.bot.run(once=True)
        self.assertEqual(count, 1)
        self.assertEqual(spy.call_count, 1)

    def test_max_cycles_limits_iterations(self):
        with patch('main.time.sleep'):  # don't actually wait
            count = self.bot.run(interval=0, max_cycles=3)
        self.assertEqual(count, 3)

    def test_killswitch_blocks_cycle_when_once(self):
        with patch.object(main_mod, 'KILLSWITCH_PATH', __file__):  # a path that exists
            with patch.object(self.bot, 'run_cycle') as never:
                count = self.bot.run(once=True)
        self.assertEqual(count, 0)
        never.assert_not_called()

    def test_parser_flags(self):
        args = build_parser().parse_args(['--once'])
        self.assertTrue(args.once)
        args = build_parser().parse_args(['--interval', '5', '--cycles', '2'])
        self.assertEqual(args.interval, 5)
        self.assertEqual(args.cycles, 2)


if __name__ == '__main__':
    unittest.main()
