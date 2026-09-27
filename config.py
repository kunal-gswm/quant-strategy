from dataclasses import dataclass, field

@dataclass
class StrategyConfig:
    ema_period: int = 50
    slope_bars: int = 5
    rsi_period: int = 14
    rsi_reclaim_level: float = 40.0
    atr_period: int = 14
    stop_atr_multiple: float = 1.5
    reward_risk_multiple: float = 2.0

@dataclass
class ExecutionConfig:
    entry_timing: str = "next_open"  
    slippage_type: str = "percentage"  
    slippage_value: float = 0.05       
    intrabar_policy: str = "conservative" 

@dataclass
class CostModelConfig:
    brokerage_type: str = "percentage"
    brokerage_value: float = 0.0
    exchange_transaction_charge_pct: float = 0.00297
    stt_pct_delivery: float = 0.10
    sebi_charges_per_crore: float = 10.0
    stamp_duty_pct_buy_leg: float = 0.015
    gst_pct: float = 18.0

@dataclass
class RiskConfig:
    max_risk_per_trade_rupees: float = 1000.0
    max_positions: int = 1
    max_daily_loss_rupees: float = 5000.0

@dataclass
class BacktestConfig:
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    cost_model: CostModelConfig = field(default_factory=CostModelConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    starting_capital: float = 500_000.0
