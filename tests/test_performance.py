import math
import unittest

from analysis.performance import summarize_trades, equity_metrics, format_report


class TestSummarizeTrades(unittest.TestCase):
    def test_empty(self):
        s = summarize_trades([])
        self.assertEqual(s['num_trades'], 0)
        self.assertEqual(s['win_rate_pct'], 0.0)
        self.assertEqual(s['profit_factor'], 0.0)

    def test_basic_stats(self):
        trades = [{'pnl': 100}, {'pnl': -50}, {'pnl': 200}, {'pnl': -50}]
        s = summarize_trades(trades)
        self.assertEqual(s['num_trades'], 4)
        self.assertEqual(s['wins'], 2)
        self.assertEqual(s['losses'], 2)
        self.assertEqual(s['win_rate_pct'], 50.0)
        self.assertAlmostEqual(s['net_pnl'], 200)
        self.assertAlmostEqual(s['gross_profit'], 300)
        self.assertAlmostEqual(s['gross_loss'], 100)
        self.assertAlmostEqual(s['profit_factor'], 3.0)
        self.assertAlmostEqual(s['avg_win'], 150)
        self.assertAlmostEqual(s['avg_loss'], 50)
        self.assertAlmostEqual(s['expectancy'], 50)

    def test_all_wins_infinite_profit_factor(self):
        s = summarize_trades([{'pnl': 10}, {'pnl': 20}])
        self.assertEqual(s['profit_factor'], float('inf'))

    def test_drawdown_of_cumulative_pnl(self):
        # +100 then -80 -> peak 100, trough 20 -> 80% drawdown of the P&L curve.
        s = summarize_trades([{'pnl': 100}, {'pnl': -80}])
        self.assertAlmostEqual(s['max_drawdown'], 80.0)

    def test_ignores_missing_pnl(self):
        s = summarize_trades([{'pnl': 10}, {'foo': 1}, {'pnl': None}])
        self.assertEqual(s['num_trades'], 1)


class TestEquityMetrics(unittest.TestCase):
    def test_return_and_drawdown(self):
        eq = equity_metrics([100000, 101000, 100500, 102000])
        self.assertAlmostEqual(eq['net_pnl'], 2000)
        self.assertAlmostEqual(eq['return_pct'], 2.0)
        # peak 101000 -> 100500 = ~0.495% drawdown
        self.assertAlmostEqual(eq['max_drawdown_pct'], (101000 - 100500) / 101000 * 100, places=4)

    def test_empty(self):
        eq = equity_metrics([])
        self.assertEqual(eq['points'], 0)
        self.assertEqual(eq['return_pct'], 0.0)


class TestFormatReport(unittest.TestCase):
    def test_renders_without_error(self):
        s = summarize_trades([{'pnl': 100}, {'pnl': -50}])
        eq = equity_metrics([10000, 10050])
        text = format_report(summary=s, equity=eq)
        self.assertIn("Performance Report", text)
        self.assertIn("Win rate", text)
        self.assertIn("Net P&L", text)

    def test_no_data_message(self):
        self.assertIn("No data yet", format_report())


if __name__ == '__main__':
    unittest.main()
