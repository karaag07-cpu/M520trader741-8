import pandas as pd
import numpy as np
from signals.base_strategy import BaseStrategy, SignalType, Conviction, Signal
from datetime import datetime
from typing import Optional

class MomentumStrategy(BaseStrategy):
    """
    Momentum + Volume Confirmation Strategy
    - Intraday: EMA 9/21 crossover with rising volume confirmation.
    - Long-term: EMA 50/200 golden/death cross with VWAP confirmation.
    """
    
    def __init__(self, name: str, timeframe: str, conviction_threshold=Conviction.MEDIUM):
        super().__init__(name, timeframe, conviction_threshold)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # EMAs
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # VWAP calculation: (Price * Volume).cumsum() / Volume.cumsum()
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Volume Trend: 20-period SMA of volume
        df['vol_sma'] = df['volume'].rolling(window=20).mean()
        
        return df

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Optional[Signal]:
        """
        Expects a pandas DataFrame with: open, high, low, close, volume.
        Optional: symbol column.
        """
        if data is None or len(data) < 200:
            return None
            
        df = self.calculate_indicators(data.copy())
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        symbol = data['symbol'].iloc[0] if 'symbol' in data.columns else "UNKNOWN"
        
        # --- BUY SIGNAL LOGIC ---
        # 1. Intraday: EMA 9/21 bullish crossover + rising volume
        # 2. Long-term: EMA 50/200 golden cross + VWAP rising
        
        ema_9_21_cross_bull = (prev_row['ema9'] <= prev_row['ema21']) and (last_row['ema9'] > last_row['ema21'])
        vol_rising = last_row['volume'] > last_row['vol_sma']
        
        ema_50_200_bull = last_row['ema50'] > last_row['ema200']
        vwap_rising = last_row['vwap'] > prev_row['vwap']
        
        # BUY if intraday setup is good AND long-term trend is bullish
        buy_signal = (ema_9_21_cross_bull and vol_rising) and (ema_50_200_bull and vwap_rising)
        
        # --- SELL/EXIT SIGNAL LOGIC ---
        # 1. Intraday: EMA 9/21 bearish crossover OR volume drop
        # 2. Long-term: EMA 50/200 death cross OR VWAP turning down
        
        ema_9_21_cross_bear = (prev_row['ema9'] >= prev_row['ema21']) and (last_row['ema9'] < last_row['ema21'])
        vol_drop = last_row['volume'] < last_row['vol_sma']
        
        ema_50_200_bear = last_row['ema50'] < last_row['ema200']
        vwap_falling = last_row['vwap'] < prev_row['vwap']
        
        sell_signal = ema_9_21_cross_bear or vol_drop or ema_50_200_bear or vwap_falling
        
        sig_type = SignalType.NEUTRAL
        conviction = Conviction.LOW
        
        if buy_signal:
            sig_type = SignalType.BUY
            # High conviction if volume is significantly higher than average
            if last_row['volume'] > (last_row['vol_sma'] * 1.5):
                conviction = Conviction.HIGH
            else:
                conviction = Conviction.MEDIUM
        elif sell_signal:
            sig_type = SignalType.SELL
            conviction = Conviction.MEDIUM
            
        if sig_type == SignalType.NEUTRAL:
            return None
            
        return Signal(
            symbol=symbol,
            type=sig_type,
            timeframe=self.timeframe,
            conviction=conviction,
            timestamp=datetime.now(),
            metadata={
                'close': float(last_row['close']),
                'ema9': float(last_row['ema9']),
                'ema21': float(last_row['ema21']),
                'vwap': float(last_row['vwap']),
                'vol_sma': float(last_row['vol_sma'])
            }
        )

# For backward compatibility if other modules still refer to RandomMomentumStrategy
RandomMomentumStrategy = MomentumStrategy
