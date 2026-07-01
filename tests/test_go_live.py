import unittest
import os
import time
from execution.paper_trader import PaperTrader
from utils.db_logger import log_trade_attempt
import subprocess

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

    def test_db_logging(self):
        # This test requires team-db to be working
        try:
            log_trade_attempt("TEST/USD", "BUY", 1.0, 50000.0, "TESTING", "Unit test log")
            
            # Verify it's in the DB
            sql = "SELECT * FROM trades WHERE symbol = 'TEST/USD' ORDER BY id DESC LIMIT 1"
            result = subprocess.run(['team-db', sql], capture_output=True, text=True)
            if result.returncode == 0:
                data = subprocess.run(['team-db', sql], capture_output=True, text=True).stdout
                # The output is JSON
                import json
                trades = json.loads(data)
                self.assertTrue(len(trades) > 0)
                self.assertEqual(trades[0]['symbol'], 'TEST/USD')
                self.assertEqual(trades[0]['status'], 'TESTING')
        except Exception as e:
            self.fail(f"DB logging test failed: {e}")

    def test_insufficient_funds(self):
        trader = PaperTrader(initial_balance=100)
        # Attempt to buy something expensive
        trade = trader.place_order("BTC/USD", "BUY", 1.0, 50000.0)
        self.assertIsNone(trade)
        
        # Verify rejection logged
        sql = "SELECT * FROM trades WHERE symbol = 'BTC/USD' AND status = 'REJECTED' ORDER BY id DESC LIMIT 1"
        result = subprocess.run(['team-db', sql], capture_output=True, text=True)
        import json
        trades = json.loads(result.stdout)
        self.assertTrue(len(trades) > 0)
        self.assertEqual(trades[0]['message'], 'Insufficient funds')

if __name__ == '__main__':
    unittest.main()
