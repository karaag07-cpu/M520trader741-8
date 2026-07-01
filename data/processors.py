import pandas as pd

def atr_series(df, period=14):
    """
    Average True Range as a full series, using Wilder's smoothing.

    True Range is the greatest of: high-low, |high - prev close|, and
    |low - prev close|. ATR is the Wilder-smoothed (RMA) average of TR over
    ``period`` bars, which is equivalent to an EWM with alpha = 1/period.
    Wilder's smoothing weights recent volatility more responsively than a
    flat rolling mean while retaining the full lookback. Values before
    ``period`` bars are NaN.

    df must contain 'high', 'low', 'close' columns.
    """
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)

    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def calculate_atr(df, period=14):
    """
    Calculates the latest Average True Range (ATR) value as a float.

    Returns ``None`` when there isn't enough data (fewer than ``period`` bars)
    to compute it. Kept scalar-returning for backwards compatibility with
    existing callers (e.g. main.py's risk step).
    """
    if df is None or df.empty or len(df) < period:
        return None

    value = atr_series(df, period).iloc[-1]
    return float(value) if pd.notna(value) else None
