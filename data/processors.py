import pandas as pd

def calculate_atr(df, period=14):
    """
    Calculates Average True Range (ATR).
    df must contain 'high', 'low', 'close' columns.
    """
    if df is None or df.empty or len(df) < period:
        return None
        
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Instruction: "Then EMA/rolling mean of True Range over the period"
    # Using simple rolling mean.
    atr_series = tr.rolling(window=period).mean()
    
    return atr_series.iloc[-1]
