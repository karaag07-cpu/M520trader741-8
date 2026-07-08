import logging
import os
import unittest
from unittest.mock import patch

from main import TradingBot


def _quiet_logger():
    lg = logging.getLogger('minutetrader.toggletest')
    lg.addHandler(logging.NullHandler())
    lg.propagate = False
    return lg


class TestAssetToggles(unittest.TestCase):
    def _bot(self):
        return TradingBot(config={}, logger=_quiet_logger())

    def test_default_trades_both(self):
        with patch.dict(os.environ, {}, clear=True):
            bot = self._bot()
        self.assertTrue(bot.symbols['crypto'])
        self.assertTrue(bot.symbols['stocks'])

    def test_disable_crypto(self):
        with patch.dict(os.environ, {'MINUTETRADER_TRADE_CRYPTO': 'false'}):
            bot = self._bot()
        self.assertEqual(bot.symbols['crypto'], [])
        self.assertTrue(bot.symbols['stocks'])  # stocks unaffected

    def test_disable_stocks(self):
        with patch.dict(os.environ, {'MINUTETRADER_TRADE_STOCKS': 'no'}):
            bot = self._bot()
        self.assertEqual(bot.symbols['stocks'], [])
        self.assertTrue(bot.symbols['crypto'])

    def test_does_not_mutate_module_default(self):
        with patch.dict(os.environ, {'MINUTETRADER_TRADE_CRYPTO': 'false'}):
            self._bot()
        import main
        self.assertTrue(main.DEFAULT_SYMBOLS['crypto'])  # module default intact

    def test_broker_env_override_selects_paper_when_off(self):
        # broker env "paper" keeps it in simulation even without keys.
        with patch.dict(os.environ, {'MINUTETRADER_BROKER': 'paper'}):
            bot = self._bot()
        self.assertIsNone(bot.broker)


if __name__ == '__main__':
    unittest.main()
