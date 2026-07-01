import unittest
from unittest.mock import patch, MagicMock
from risk.risk_manager import RiskManager
from execution.paper_trader import PaperTrader


class TestPositionSizing(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def test_risk_based_size(self):
        # Risk 1% of 10,000 = 100 over a 1-point stop distance -> 100 units,
        # capped by buying power (10000/100 = 100). min(100, 100) = 100.
        size = self.rm.calculate_position_size(10000, 100.0, 99.0, risk_per_trade=0.01)
        self.assertAlmostEqual(size, 100.0)

    def test_wider_stop_smaller_size(self):
        # 100 risk capital over a 5-point stop -> 20 units.
        size = self.rm.calculate_position_size(10000, 100.0, 95.0, risk_per_trade=0.01)
        self.assertAlmostEqual(size, 20.0)

    def test_size_capped_by_buying_power(self):
        # Tiny stop distance would imply a huge size; cap at balance/entry.
        size = self.rm.calculate_position_size(10000, 100.0, 99.999, risk_per_trade=0.01)
        self.assertAlmostEqual(size, 100.0)  # 10000 / 100

    def test_zero_stop_distance_returns_zero(self):
        self.assertEqual(self.rm.calculate_position_size(10000, 100.0, 100.0), 0.0)

    def test_non_positive_balance_returns_zero(self):
        self.assertEqual(self.rm.calculate_position_size(0, 100.0, 99.0), 0.0)

    def test_invalid_risk_fraction_raises(self):
        with self.assertRaises(ValueError):
            self.rm.calculate_position_size(10000, 100.0, 99.0, risk_per_trade=1.5)


class TestPaperTraderPortfolio(unittest.TestCase):
    @patch('utils.db_logger.subprocess.run')
    def test_portfolio_value_includes_open_positions(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        trader = PaperTrader(initial_balance=100000)
        trader.place_order("BTC/USD", "BUY", 1.0, 100.0,
                           stop_loss=95.0, take_profit=130.0)
        # Marked up to 120 -> +20 unrealised on top of cash balance.
        self.assertAlmostEqual(trader.get_portfolio_value({"BTC/USD": 120.0}), 100020.0)

    @patch('utils.db_logger.subprocess.run')
    def test_close_all_positions_flattens(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        trader = PaperTrader(initial_balance=100000)
        trader.place_order("BTC/USD", "BUY", 1.0, 100.0,
                           stop_loss=95.0, take_profit=130.0)
        trader.place_order("ETH/USD", "BUY", 2.0, 50.0,
                           stop_loss=45.0, take_profit=70.0)

        closed = trader.close_all_positions({"BTC/USD": 110.0, "ETH/USD": 55.0})

        self.assertEqual(closed, 2)
        self.assertEqual(len(trader.positions), 0)
        self.assertEqual(len(trader.trade_history), 2)
        # BTC +10 (1 unit), ETH +10 (2 units * 5) -> balance +20
        self.assertAlmostEqual(trader.balance, 100020.0)

    @patch('utils.db_logger.subprocess.run')
    def test_close_all_positions_without_price_uses_entry(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        trader = PaperTrader(initial_balance=100000)
        trader.place_order("BTC/USD", "BUY", 1.0, 100.0,
                           stop_loss=95.0, take_profit=130.0)
        # No price supplied -> close at entry, zero P&L, still flattened.
        closed = trader.close_all_positions()
        self.assertEqual(closed, 1)
        self.assertEqual(len(trader.positions), 0)
        self.assertAlmostEqual(trader.balance, 100000.0)


if __name__ == '__main__':
    unittest.main()
