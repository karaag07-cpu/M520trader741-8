import pandas as pd
import numpy as np
from signals.base_strategy import BaseStrategy, SignalType, Conviction, Signal
from datetime import datetime
from typing import Optional

class RelativeStrengthStrategy(BaseStrategy):
    """
    Relative Strength / Flow Detection Strategy
    - Volume spike: 2.5x SMA(20)
    - Support: Min(Low, 14)
    - RS: Asset outperforming Benchmark over last 20 periods
    """
    
    def __init__(self, name: str, timeframe: str, conviction_threshold=Conviction.MEDIUM):
        super().__init__(name, timeframe, conviction_threshold)

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Optional[Signal]:
        benchmark_data = kwargs.get('benchmark_data')
        
        if data is None or len(data) < 20:
            return None
            
        # Support Level: Min of Lows over last 14 periods
        # We'll work on a copy to avoid modifying the original df
        df = data.copy()
        df['support'] = df['low'].rolling(window=14).min()
        
        # Volume SMA
        df['vol_sma'] = df['volume'].rolling(window=20).mean()
        
        last_row = df.iloc[-1]
        
        # 1. Volume Spike
        vol_spike = last_row['volume'] > 2.5 * last_row['vol_sma']
        
        # 2. Price above Support
        # Note: Support is usually from the *previous* periods to check if current is holding
        # but the spec says "Price(0) > Support(14)". 
        # Usually that means current price is higher than the minimum of the last 14 lows.
        above_support = last_row['close'] > last_row['support']
        
        # 3. Relative Strength
        rs_ok = True
        rs_value = 1.0
        if benchmark_data is not None and len(benchmark_data) >= 20:
            # Simple RS: (Asset_Close / Asset_Start) / (Bench_Close / Bench_Start)
            asset_close = last_row['close']
            asset_start = df.iloc[-20]['close']
            
            bench_close = benchmark_data.iloc[-1]['close']
            bench_start = benchmark_data.iloc[-20]['close']
            
            if asset_start > 0 and bench_start > 0:
                rs_value = (asset_close / asset_start) / (bench_close / bench_start)
                rs_ok = rs_value > 1.0
            
        # Conviction Score: High if all 3 met; Medium if 1 & 2 met.
        sig_type = SignalType.NEUTRAL
        conviction = Conviction.LOW
        
        if vol_spike and above_support:
            sig_type = SignalType.BUY
            if rs_ok:
                conviction = Conviction.HIGH
            else:
                conviction = Conviction.MEDIUM
        
        # Exit Rules: Support break OR Volume normalization
        # Spec says: Exit if Volume < 1.2x SMA OR Price < Support
        # But we'll only trigger SELL signal if it was previously a BUY.
        # Actually, for the signal generator, we just return current state.
        if last_row['close'] < last_row['support']:
            sig_type = SignalType.SELL
            conviction = Conviction.MEDIUM
        elif last_row['volume'] < 1.2 * last_row['vol_sma'] and vol_spike == False:
            # This is more of an 'EXIT' than a 'SELL' but we'll use SELL/NEUTRAL
            # Let's use NEUTRAL if it's just normalizing volume
            pass
            
        if sig_type == SignalType.NEUTRAL:
            return None
            
        symbol = df.attrs.get('symbol', 'UNKNOWN')
        if 'symbol' in df.columns:
            symbol = df['symbol'].iloc[0]
            
        return Signal(
            symbol=symbol,
            type=sig_type,
            timeframe=self.timeframe,
            conviction=conviction,
            timestamp=datetime.now(),
            metadata={
                'volume_spike': bool(vol_spike),
                'above_support': bool(above_support),
                'rs_value': float(rs_value),
                'support_level': float(last_row['support']),
                'strategy_name': self.name
            }
        )
