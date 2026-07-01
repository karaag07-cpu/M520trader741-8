from signals.base_strategy import BaseStrategy, Signal, SignalType, Conviction
from datetime import datetime
from typing import Optional

class MacroRegimeStrategy(BaseStrategy):
    def __init__(self, name="MacroRegimeDetection", timeframe="Daily"):
        super().__init__(name, timeframe)

    def generate_signal(self, data, **kwargs) -> Optional[Signal]:
        """
        Accepts macro data via kwargs:
        - yc_spread: float (T10Y2Y)
        - inflation_yoy: float (CPI Year-over-Year %)
        - fed_rate_trend: str ("Rising", "Falling", "Stable")
        - unrate_trend: str ("Rising", "Falling", "Stable") (Optional)
        """
        yc_spread = kwargs.get('yc_spread', 1.0)
        inflation_yoy = kwargs.get('inflation_yoy', 2.0)
        fed_rate_trend = kwargs.get('fed_rate_trend', "Stable")
        unrate_trend = kwargs.get('unrate_trend', "Stable")

        regime = "Normal Expansion"
        bias = "BULLISH"
        modifier = 1.0
        conviction = Conviction.LOW

        # Logic from macro_regime_model.md
        if yc_spread < 0:
            regime = "Deflationary Bust"
            bias = "BEARISH"
            modifier = 0.0
            conviction = Conviction.HIGH
        elif inflation_yoy > 4.0 and fed_rate_trend == "Rising":
            regime = "Overheating"
            bias = "NEUTRAL"
            modifier = 0.5
            conviction = Conviction.MEDIUM
        elif yc_spread > 0.5 and inflation_yoy < 3.0:
            regime = "Goldilocks"
            bias = "BULLISH"
            modifier = 1.0
            conviction = Conviction.HIGH
        elif yc_spread > 0 and yc_spread < 0.5 and fed_rate_trend == "Falling":
            regime = "Reflation"
            bias = "BULLISH"
            modifier = 1.0
            conviction = Conviction.MEDIUM

        metadata = {
            'regime': regime,
            'global_bias': bias,
            'position_size_modifier': modifier,
            'yc_spread': yc_spread,
            'inflation_yoy': inflation_yoy,
            'fed_rate_trend': fed_rate_trend
        }

        return Signal(
            symbol="GLOBAL",
            type=SignalType.NEUTRAL,
            timeframe=self.timeframe,
            conviction=conviction,
            metadata=metadata
        )
