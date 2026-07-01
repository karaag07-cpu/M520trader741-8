import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_ohlcv(symbol, length=300, timeframe_mins=15):
    """
    Generates mock OHLCV data for testing.
    """
    start_time = datetime.now() - timedelta(minutes=length * timeframe_mins)
    timestamps = [start_time + timedelta(minutes=i * timeframe_mins) for i in range(length)]
    
    # Generate a random walk for price
    price = 50000.0 if "BTC" in symbol else 3000.0
    prices = []
    for _ in range(length):
        price += np.random.normal(0, price * 0.001)
        prices.append(price)
        
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': prices,
        'high': [p * 1.002 for p in prices],
        'low': [p * 0.998 for p in prices],
        'close': [p * 1.001 for p in prices],
        'volume': np.random.randint(100, 1000, size=length).astype(float)
    })
    
    df['symbol'] = symbol
    return df
