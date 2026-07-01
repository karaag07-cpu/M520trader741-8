"""Technical indicator calculations used across the bot."""
import pandas as pd


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (Wilder's smoothing).

    True Range is the greatest of: current high-low, |high - prev close|,
    |low - prev close|. ATR is the Wilder-smoothed (RMA) average of TR over
    ``period`` bars. Values before ``period`` bars are NaN.

    Requires 'high', 'low', 'close' columns.
    """
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)

    true_range = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Wilder's smoothing == EWM with alpha = 1/period.
    return true_range.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def latest_atr(df: pd.DataFrame, period: int = 14):
    """Return the most recent ATR value as a float, or None if there isn't
    enough data (fewer than ``period`` bars) to compute it."""
    if df is None or len(df) < period:
        return None
    value = calculate_atr(df, period).iloc[-1]
    return float(value) if pd.notna(value) else None
