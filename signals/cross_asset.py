from typing import Optional, Dict
from signals.base_strategy import BaseStrategy, SignalType, Conviction, Signal
import pandas as pd
from datetime import datetime

class CrossAssetStrategy(BaseStrategy):
    """
    Cross-Asset Leading Signals Strategy
    - Monitors DXY, US10Y, BTC as leaders.
    - Pauses or enables other strategies based on leader moves.
    """
    def __init__(self, name: str, timeframe: str):
        super().__init__(name, timeframe)

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Optional[Signal]:
        # 'data' here is the Target asset data, but we mainly care about 'leaders' in kwargs
        leaders = kwargs.get('leaders', {})
        if not leaders:
            return None

        symbol = data.attrs.get('symbol', 'UNKNOWN')
        if 'symbol' in data.columns:
            symbol = data['symbol'].iloc[0]
            
        bias_metadata = {}
        
        # 1. DXY -> Crypto (Inverse)
        # Specs: 15m DXY change > 0.1% triggers action (Bearish regime)
        if 'DXY' in leaders and leaders['DXY'] is not None:
            dxy_df = leaders['DXY']
            if len(dxy_df) >= 2:
                dxy_close = dxy_df['close'].iloc[-1]
                dxy_prev = dxy_df['close'].iloc[-2]
                dxy_change = (dxy_close / dxy_prev) - 1
                if dxy_change > 0.001:
                    bias_metadata['dxy_spike'] = True
                    bias_metadata['crypto_bias'] = 'BEARISH'
                elif dxy_change < -0.001:
                    bias_metadata['dxy_drop'] = True
                    bias_metadata['crypto_bias'] = 'BULLISH'
        
        # 2. US10Y Yield -> Tech (Inverse)
        # Specs: Daily change > 0.05 (5 bps) triggers bearish action
        if 'US10Y' in leaders and leaders['US10Y'] is not None:
            yield_df = leaders['US10Y']
            if len(yield_df) >= 2:
                yield_close = yield_df['close'].iloc[-1]
                yield_prev = yield_df['close'].iloc[-2]
                yield_change = yield_close - yield_prev
                if yield_change > 0.05:
                    bias_metadata['yield_spike'] = True
                    bias_metadata['tech_bias'] = 'BEARISH'
                elif yield_change < -0.05:
                    bias_metadata['yield_drop'] = True
                    bias_metadata['tech_bias'] = 'BULLISH'
        
        # 3. BTC -> Altcoins (Positive)
        # Specs: 5m BTC change > 0.5% triggers action
        # Note: we check if the current symbol is an altcoin
        is_altcoin = symbol not in ['BTC/USDT', 'BTC', 'WBTC']
        if 'BTC' in leaders and leaders['BTC'] is not None and is_altcoin:
            btc_df = leaders['BTC']
            if len(btc_df) >= 2:
                btc_close = btc_df['close'].iloc[-1]
                btc_prev = btc_df['close'].iloc[-2]
                btc_change = (btc_close / btc_prev) - 1
                if btc_change > 0.005:
                    bias_metadata['btc_breakout'] = True
                    bias_metadata['altcoin_bias'] = 'BULLISH'
                elif btc_change < -0.005:
                    bias_metadata['btc_breakdown'] = True
                    bias_metadata['altcoin_bias'] = 'BEARISH'

        if not bias_metadata:
            return None

        # Return a NEUTRAL signal with bias metadata
        # Neutral signals are used as filters by the Combiner or Main Loop
        return Signal(
            symbol=symbol,
            type=SignalType.NEUTRAL,
            timeframe=self.timeframe,
            conviction=Conviction.MEDIUM,
            timestamp=datetime.now(),
            metadata={
                'bias': bias_metadata,
                'strategy_name': self.name
            }
        )
