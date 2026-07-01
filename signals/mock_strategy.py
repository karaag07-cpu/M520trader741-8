from signals.base_strategy import BaseStrategy, Signal, SignalType, Conviction
import pandas as pd
from datetime import datetime

class MockStrategy(BaseStrategy):
    def __init__(self, name, timeframe, signal_type=SignalType.BUY, conviction=Conviction.LOW):
        super().__init__(name, timeframe)
        self.signal_type = signal_type
        self.conviction = conviction

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        # Get symbol from metadata if available, else default
        symbol = df.attrs.get('symbol', 'UNKNOWN')
        return Signal(
            symbol=symbol,
            type=self.signal_type,
            timeframe=self.timeframe,
            conviction=self.conviction,
            timestamp=datetime.now(),
            metadata={'strategy_name': self.name}
        )
