from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime

class Conviction(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"

@dataclass
class Signal:
    symbol: str
    type: SignalType
    timeframe: str
    conviction: Conviction
    timestamp: datetime = field(default_factory=datetime.now)
    entry_zone: Optional[Tuple[float, float]] = None
    tp_levels: List[float] = field(default_factory=list)
    stop_loss: Optional[float] = None
    metadata: dict = field(default_factory=dict)

class BaseStrategy(ABC):
    def __init__(self, name, timeframe, conviction_threshold=Conviction.MEDIUM):
        self.name = name
        self.timeframe = timeframe
        self.conviction_threshold = conviction_threshold

    @abstractmethod
    def generate_signal(self, data, **kwargs) -> Optional[Signal]:
        """
        Processes data and returns a Signal object or None if no signal.
        """
        pass
