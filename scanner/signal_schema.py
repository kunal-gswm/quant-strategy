from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Signal:
    strategy_version: str
    signal_id: str
    symbol: str
    signal_timestamp: str
    direction: str
    signal_price: float
    planned_entry: float
    stop_loss: float
    target: float
    risk_per_share: float
    reward_per_share: float
    risk_reward_ratio: float
    atr: float
    ema50: float
    rsi14: float
    trend_slope: float
    position_size: int
    capital_at_risk: float
    risk_percent: float
    data_timestamp: str
    data_freshness: str
    signal_status: str
    signal_reason: str
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self):
        return {
            "signal_id": self.signal_id,
            "strategy_version": self.strategy_version,
            "symbol": self.symbol,
            "signal_timestamp": self.signal_timestamp,
            "direction": self.direction,
            "signal_price": self.signal_price,
            "planned_entry": self.planned_entry,
            "stop_loss": self.stop_loss,
            "target": self.target,
            "risk_per_share": self.risk_per_share,
            "reward_per_share": self.reward_per_share,
            "risk_reward_ratio": self.risk_reward_ratio,
            "atr": self.atr,
            "ema50": self.ema50,
            "rsi14": self.rsi14,
            "trend_slope": self.trend_slope,
            "position_size": self.position_size,
            "capital_at_risk": self.capital_at_risk,
            "risk_percent": self.risk_percent,
            "data_timestamp": self.data_timestamp,
            "data_freshness": self.data_freshness,
            "signal_status": self.signal_status,
            "signal_reason": self.signal_reason,
            "created_at": self.created_at,
        }
