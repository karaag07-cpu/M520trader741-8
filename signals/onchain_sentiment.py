import pandas as pd
import numpy as np
from signals.base_strategy import BaseStrategy, SignalType, Conviction, Signal
from datetime import datetime
from typing import Optional

class OnChainSentimentStrategy(BaseStrategy):
    """
    On-Chain & Sentiment Strategy (Crypto focused)
    - Monitors Exchange Net Flow, MVRV Ratio, and Funding Rates.
    """
    def __init__(self, name: str, timeframe: str):
        super().__init__(name, timeframe)

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Optional[Signal]:
        # 'data' is OHLCV, but we need on-chain data from kwargs
        # In a real scenario, this would come from an API like Glassnode or CryptoQuant
        onchain = kwargs.get('onchain', {})
        
        # Use provided data or default to neutral values
        net_flow_z = onchain.get('net_flow_z', 0.0)
        mvrv_ratio = onchain.get('mvrv_ratio', 1.5)
        funding_rate = onchain.get('funding_rate', 0.01) # 0.01%
        
        symbol = data.attrs.get('symbol', 'UNKNOWN')
        if 'symbol' in data.columns:
            symbol = data['symbol'].iloc[0]
            
        # Bullish/Bearish Thresholds from specs
        # Bullish: Net Flow < -2 Std Dev, MVRV < 1.0, Funding < 0%
        # Bearish: Net Flow > +2 Std Dev, MVRV > 3.0, Funding > 0.03%
        
        is_bullish_flow = net_flow_z < -2.0
        is_bullish_mvrv = mvrv_ratio < 1.0
        is_bullish_funding = funding_rate < 0
        
        is_bearish_flow = net_flow_z > 2.0
        is_bearish_mvrv = mvrv_ratio > 3.0
        is_bearish_funding = funding_rate > 0.03
        
        sig_type = SignalType.NEUTRAL
        conviction = Conviction.LOW
        
        # High Conviction Bullish: Net Flow negative AND MVRV < 1.2 AND Funding < 0.01%
        if net_flow_z < 0 and mvrv_ratio < 1.2 and funding_rate < 0.01:
            sig_type = SignalType.BUY
            conviction = Conviction.HIGH
        elif is_bullish_flow or is_bullish_mvrv or is_bullish_funding:
            sig_type = SignalType.BUY
            conviction = Conviction.MEDIUM
        elif is_bearish_flow or is_bearish_mvrv or is_bearish_funding:
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
                'net_flow_z': net_flow_z,
                'mvrv_ratio': mvrv_ratio,
                'funding_rate': funding_rate,
                'strategy_name': self.name
            }
        )
