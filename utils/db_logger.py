import subprocess
import json
import logging

logger = logging.getLogger('MinuteTrader.DBLogger')

def log_trade_attempt(symbol, side, amount, price, status, message=""):
    """
    Logs a trade attempt to the shared Turso database using the team-db CLI.
    """
    sql = f"INSERT INTO trades (symbol, side, amount, price, status, message) VALUES ('{symbol}', '{side}', {amount}, {price}, '{status}', '{message}')"
    try:
        # team-db "SQL"
        result = subprocess.run(['team-db', sql], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to log trade to DB: {result.stderr}")
        else:
            logger.debug(f"Trade logged to DB: {symbol} {side}")
    except Exception as e:
        logger.error(f"Error calling team-db: {e}")
