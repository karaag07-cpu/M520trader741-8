from typing import List, Optional
from signals.base_strategy import Signal, SignalType, Conviction
from datetime import datetime

class SignalCombiner:
    """
    Combines signals from multiple strategies into a single consensus signal.
    """
    
    def __init__(self, conviction_weights=None):
        # Default weights
        self.weights = conviction_weights or {
            Conviction.LOW: 1,
            Conviction.MEDIUM: 2,
            Conviction.HIGH: 3
        }

    def combine(self, signals: List[Signal], symbol: str) -> Optional[Signal]:
        if not signals:
            return None
            
        net_score = 0
        contributing_strategies = []
        
        for sig in signals:
            if sig.symbol != symbol:
                continue
                
            weight = self.weights.get(sig.conviction, 1)
            
            if sig.type == SignalType.BUY:
                net_score += weight
                contributing_strategies.append(f"{sig.metadata.get('strategy_name', 'Unknown')}(BUY:{sig.conviction.name})")
            elif sig.type == SignalType.SELL:
                net_score -= weight
                contributing_strategies.append(f"{sig.metadata.get('strategy_name', 'Unknown')}(SELL:{sig.conviction.name})")
                
        if net_score == 0:
            return None
            
        final_type = SignalType.BUY if net_score > 0 else SignalType.SELL
        abs_score = abs(net_score)
        
        # Map absolute score back to conviction
        if abs_score <= 2:
            final_conviction = Conviction.LOW
        elif abs_score <= 5:
            final_conviction = Conviction.MEDIUM
        else:
            final_conviction = Conviction.HIGH
            
        return Signal(
            symbol=symbol,
            type=final_type,
            timeframe="combined",
            conviction=final_conviction,
            timestamp=datetime.now(),
            metadata={
                'net_score': net_score,
                'contributions': ", ".join(contributing_strategies)
            }
        )
