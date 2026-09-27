from dataclasses import dataclass
from enum import Enum

class ExitReason(Enum):
    STOP = "STOP"
    TARGET = "TARGET"
    END_OF_DATA = "END_OF_DATA"

@dataclass
class OpenPosition:
    entry_price: float
    stop_price: float
    target_price: float
    quantity: int
    entry_timestamp: object
    signal_timestamp: object = None
    atr_at_signal: float = 0.0

def check_exit(position: OpenPosition, bar_high: float, bar_low: float,
               intrabar_policy: str = "conservative"):
    hit_stop = bar_low <= position.stop_price
    hit_target = bar_high >= position.target_price
    
    if hit_stop and hit_target:
        if intrabar_policy == "conservative":
            return ExitReason.STOP, position.stop_price, True
        raise NotImplementedError("Only 'conservative' policy is in V1.0 scope")
    if hit_stop:
        return ExitReason.STOP, position.stop_price, False
    if hit_target:
        return ExitReason.TARGET, position.target_price, False
    return None, None, False
