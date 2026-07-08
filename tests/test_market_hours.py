import unittest
from datetime import datetime

from main import equity_market_open, in_flatten_window


class TestMarketHours(unittest.TestCase):
    # 2026-07-06 is a Monday; 2026-07-11 is a Saturday.
    def test_open_midday_weekday(self):
        self.assertTrue(equity_market_open(datetime(2026, 7, 6, 11, 0)))

    def test_closed_before_open(self):
        self.assertFalse(equity_market_open(datetime(2026, 7, 6, 9, 0)))

    def test_closed_after_close(self):
        self.assertFalse(equity_market_open(datetime(2026, 7, 6, 16, 30)))

    def test_closed_on_weekend(self):
        self.assertFalse(equity_market_open(datetime(2026, 7, 11, 11, 0)))

    def test_open_exactly_at_930(self):
        self.assertTrue(equity_market_open(datetime(2026, 7, 6, 9, 30)))

    def test_flatten_window_active(self):
        self.assertTrue(in_flatten_window(datetime(2026, 7, 6, 15, 56)))

    def test_flatten_window_inactive_midday(self):
        self.assertFalse(in_flatten_window(datetime(2026, 7, 6, 11, 0)))

    def test_flatten_window_inactive_after_close(self):
        self.assertFalse(in_flatten_window(datetime(2026, 7, 6, 16, 1)))

    def test_flatten_window_inactive_weekend(self):
        self.assertFalse(in_flatten_window(datetime(2026, 7, 11, 15, 56)))

    def test_none_is_safe(self):
        # If timezone data is unavailable, both must return False (no action).
        self.assertFalse(equity_market_open(None))
        self.assertFalse(in_flatten_window(None))


if __name__ == '__main__':
    unittest.main()
