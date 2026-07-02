import logging
import unittest
from unittest.mock import patch, MagicMock

from utils.db_logger import log_trade_attempt, _sql_str, _sql_num


class TestDbLogger(unittest.TestCase):
    def test_missing_team_db_does_not_error(self):
        # Simulate the CLI being absent (Windows raises FileNotFoundError).
        with patch('utils.db_logger.subprocess.run', side_effect=FileNotFoundError()):
            with self.assertLogs('MinuteTrader.DBLogger', level='DEBUG') as cm:
                log_trade_attempt('BTC/USD', 'BUY', 1.0, 100.0, 'EXECUTED')
        # Quietly noted at debug, NOT an error.
        joined = "\n".join(cm.output)
        self.assertIn('DEBUG', joined)
        self.assertNotIn('ERROR', joined)

    def test_missing_team_db_never_raises(self):
        with patch('utils.db_logger.subprocess.run', side_effect=FileNotFoundError()):
            # Must not propagate — trade execution should never be blocked by logging.
            log_trade_attempt('X', 'BUY', 1.0, 1.0, 'EXECUTED')

    def test_successful_call_still_logs_sql(self):
        with patch('utils.db_logger.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
            log_trade_attempt("O'Brien", 'BUY', 2.0, 50.0, 'EXECUTED', "it's fine")
            sql = mock_run.call_args[0][0][1]
        self.assertIn("INSERT INTO trades", sql)
        self.assertIn("'O''Brien'", sql)   # injection-safe escaping preserved
        self.assertIn("'it''s fine'", sql)

    def test_real_error_still_logged_as_error(self):
        with patch('utils.db_logger.subprocess.run', side_effect=RuntimeError('boom')):
            with self.assertLogs('MinuteTrader.DBLogger', level='ERROR') as cm:
                log_trade_attempt('X', 'BUY', 1.0, 1.0, 'EXECUTED')
        self.assertIn('boom', "\n".join(cm.output))

    def test_sql_helpers(self):
        self.assertEqual(_sql_str("a'b"), "'a''b'")
        self.assertEqual(_sql_num(3), "3.0")


if __name__ == '__main__':
    unittest.main()
