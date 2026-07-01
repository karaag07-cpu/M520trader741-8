import os
import unittest
from unittest.mock import patch

from utils.logger import default_log_path


class TestDefaultLogPath(unittest.TestCase):
    def test_env_override_is_used(self):
        with patch.dict(os.environ, {'MINUTETRADER_LOG_DIR': '/var/log/mt'}):
            self.assertEqual(default_log_path('bot.log'), '/var/log/mt/bot.log')

    def test_defaults_to_logs_dir_at_project_root(self):
        with patch.dict(os.environ, {}, clear=True):
            path = default_log_path('bot.log')
        self.assertTrue(path.endswith(os.path.join('logs', 'bot.log')))
        # Resolves to an absolute path, not a machine-specific hardcoded one.
        self.assertTrue(os.path.isabs(path))
        self.assertNotIn('/home/team', path)

    def test_project_root_logs_dir_is_repo_relative(self):
        with patch.dict(os.environ, {}, clear=True):
            path = default_log_path('x.log')
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertEqual(path, os.path.join(repo_root, 'logs', 'x.log'))


if __name__ == '__main__':
    unittest.main()
