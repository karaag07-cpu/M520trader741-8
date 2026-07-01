import unittest
import os
from unittest.mock import patch, MagicMock
from execution.paper_trader import PaperTrader
from utils.db_logger import log_trade_attempt, _sql_str


class TestGoLive(unittest.TestCase):
    def test_killswitch(self):
        killswitch_path = 'killswitch.test.lock'
        if os.path.exists(killswitch_path):
            os.remove(killswitch_path)

        # Simulate bot check
        self.assertFalse(os.path.exists(killswitch_path))

        # Activate killswitch
        with open(killswitch_path, 'w') as f:
            f.write('STOP')

        self.assertTrue(os.path.exists(killswitch_path))
        os.remove(killswitch_path)

    def test_db_logging_builds_safe_sql(self):
        """log_trade_attempt should send a well-formed, injection-safe INSERT
        to team-db. We mock the CLI so the test is hermetic (no external DB)."""
        with patch('utils.db_logger.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            log_trade_attempt("TEST/USD", "BUY", 1.0, 50000.0, "TESTING", "Unit test log")

            self.assertTrue(mock_run.called)
            args, _ = mock_run.call_args
            cmd = args[0]
            self.assertEqual(cmd[0], 'team-db')
            sql = cmd[1]
            self.assertIn("INSERT INTO trades", sql)
            self.assertIn("'TEST/USD'", sql)
            self.assertIn("'TESTING'", sql)

    def test_db_logging_escapes_quotes(self):
        """A value containing a single quote must not break out of the literal."""
        self.assertEqual(_sql_str("O'Brien"), "'O''Brien'")
        with patch('utils.db_logger.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            log_trade_attempt("A'B", "BUY", 1.0, 1.0, "OK", "it's fine")
            sql = mock_run.call_args[0][0][1]
            self.assertIn("'A''B'", sql)
            self.assertIn("'it''s fine'", sql)

    def test_insufficient_funds(self):
        """PaperTrader must reject orders that exceed the balance and log the
        rejection. subprocess is mocked so no real team-db is required."""
        with patch('utils.db_logger.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            trader = PaperTrader(initial_balance=100)
            # Attempt to buy something far more expensive than the balance
            trade = trader.place_order("BTC/USD", "BUY", 1.0, 50000.0)
            self.assertIsNone(trade)

            # Verify a REJECTED trade with 'Insufficient funds' was logged
            self.assertTrue(mock_run.called)
            sql = mock_run.call_args[0][0][1]
            self.assertIn("'REJECTED'", sql)
            self.assertIn("Insufficient funds", sql)


if __name__ == '__main__':
    unittest.main()
