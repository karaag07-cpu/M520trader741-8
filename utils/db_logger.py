import subprocess
import logging

logger = logging.getLogger('MinuteTrader.DBLogger')


def _sql_str(value) -> str:
    """Return a safely-quoted SQL string literal.

    Single quotes are escaped by doubling them, per the SQL standard, so that
    values containing apostrophes (e.g. ``O'Brien``) or crafted input cannot
    break out of the literal or inject additional statements.
    """
    return "'" + str(value).replace("'", "''") + "'"


def _sql_num(value) -> str:
    """Return a numeric SQL literal, validating the input is really numeric."""
    return repr(float(value))


def log_trade_attempt(symbol, side, amount, price, status, message=""):
    """
    Logs a trade attempt to the shared Turso database using the team-db CLI.

    Values are rendered as properly-escaped SQL literals to avoid injection or
    breakage on inputs containing quote characters.
    """
    sql = (
        "INSERT INTO trades (symbol, side, amount, price, status, message) "
        "VALUES ("
        f"{_sql_str(symbol)}, {_sql_str(side)}, {_sql_num(amount)}, "
        f"{_sql_num(price)}, {_sql_str(status)}, {_sql_str(message)})"
    )
    try:
        # team-db "SQL"
        result = subprocess.run(['team-db', sql], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed to log trade to DB: {result.stderr}")
        else:
            logger.debug(f"Trade logged to DB: {symbol} {side}")
    except FileNotFoundError:
        # The team-db CLI isn't installed (the common case outside the original
        # team's infra). DB logging is optional, so note it quietly rather than
        # spamming an error on every trade — the trade itself still executes.
        logger.debug("team-db CLI not found; skipping trade DB logging")
    except Exception as e:
        logger.error(f"Error calling team-db: {e}")
