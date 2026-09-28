from dataclasses import dataclass, field
from config import StrategyConfig, ExecutionConfig, CostModelConfig, RiskConfig, BacktestConfig

STRATEGY_VERSION = "TPQSE_v1.0"
UNIVERSE_NAME = "CURRENT_ACTIVE_UNIVERSE"
SURVIVORSHIP_STATUS = "UNRESOLVED"

def get_frozen_forward_config() -> BacktestConfig:
    """
    Returns the explicitly frozen strategy configuration for TPQSE_v1.0.
    DO NOT MODIFY THESE PARAMETERS ONCE FORWARD TESTING BEGINS.
    """
    return BacktestConfig(
        strategy=StrategyConfig(
            ema_period=50,
            slope_bars=5,
            rsi_period=14,
            rsi_reclaim_level=40.0,
            atr_period=14,
            stop_atr_multiple=1.5,
            reward_risk_multiple=2.0
        ),
        execution=ExecutionConfig(
            entry_timing="next_open",
            slippage_type="percentage",
            slippage_value=0.05,
            intrabar_policy="conservative"
        ),
        cost_model=CostModelConfig(
            brokerage_type="percentage",
            brokerage_value=0.0,
            exchange_transaction_charge_pct=0.00297,
            stt_pct_delivery=0.10,
            sebi_charges_per_crore=10.0,
            stamp_duty_pct_buy_leg=0.015,
            gst_pct=18.0
        ),
        risk=RiskConfig(
            max_risk_per_trade_rupees=1000.0,
            max_positions=1, # This is a placeholder; portfolio engine handles sizing via risk_pct
            max_daily_loss_rupees=5000.0
        ),
        starting_capital=1_000_000.0
    )
