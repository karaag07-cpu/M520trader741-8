import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def validate_correlation(leader_sym, lag_sym, lags=[0, 5, 15, 30, 60], interval='15m', period='30d'):
    print(f"\nValidating Correlation: {leader_sym} -> {lag_sym} ({interval})")
    
    # Fetch data
    leader_data = yf.download(leader_sym, period=period, interval=interval)
    lag_data = yf.download(lag_sym, period=period, interval=interval)
    
    if leader_data.empty or lag_data.empty:
        print(f"  Error: No data for {leader_sym} or {lag_sym}")
        return {}

    # Extract Close series, handling potential MultiIndex
    if isinstance(leader_data.columns, pd.MultiIndex):
        leader_close = leader_data['Close'][leader_sym]
    else:
        leader_close = leader_data['Close']
        
    if isinstance(lag_data.columns, pd.MultiIndex):
        lag_close = lag_data['Close'][lag_sym]
    else:
        lag_close = lag_data['Close']
    
    # Align data
    df = pd.DataFrame({'leader': leader_close, 'lag': lag_close}).dropna()
    
    # Calculate returns
    df['leader_ret'] = df['leader'].pct_change()
    df['lag_ret'] = df['lag'].pct_change()
    df = df.dropna()
    
    results = {}
    for lag in lags:
        # Convert lag (minutes) to number of periods
        if interval.endswith('m'):
            interval_mins = int(interval.replace('m', ''))
            shift_periods = lag // interval_mins
        elif interval.endswith('h'):
            interval_mins = int(interval.replace('h', '')) * 60
            shift_periods = lag // interval_mins
        elif interval == '1d':
            shift_periods = lag # In days for '1d' interval
        else:
            shift_periods = lag
        
        if shift_periods == 0:
            corr = df['leader_ret'].corr(df['lag_ret'])
        else:
            corr = df['leader_ret'].shift(shift_periods).corr(df['lag_ret'])
        
        results[f"{lag}m lag"] = corr
        print(f"  Lag {lag}m: {corr:.4f}")
    
    return results

if __name__ == "__main__":
    # Assumptions to test:
    # 1. DXY -> BTC (Inverse)
    validate_correlation('DX-Y.NYB', 'BTC-USD', lags=[0, 15, 30, 60], interval='15m', period='30d')
    
    # 2. US10Y -> QQQ (Inverse)
    # Using 1d to avoid intraday mismatch for now, or just fillna
    validate_correlation('^TNX', 'QQQ', lags=[0, 1], interval='1d', period='60d')
    
    # 3. BTC -> ETH (Positive) - 1m data for more precision
    validate_correlation('BTC-USD', 'ETH-USD', lags=[0, 1, 2, 5], interval='1m', period='7d')
    
    # 4. BTC -> SOL (Positive)
    validate_correlation('BTC-USD', 'SOL-USD', lags=[0, 1, 2, 5], interval='1m', period='7d')
