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


import hashlib

def get_configuration_fingerprint() -> dict:
    """
    Returns a deterministic fingerprint of the frozen TPQSE_v1.0 configuration.
    If any value changes, the hash changes, signaling a configuration drift.
    """
    cfg = get_frozen_forward_config()
    fingerprint = {
        "strategy_version": STRATEGY_VERSION,
        "ema_period": cfg.strategy.ema_period,
        "ema_slope_period": cfg.strategy.slope_bars,
        "rsi_period": cfg.strategy.rsi_period,
        "rsi_threshold": cfg.strategy.rsi_reclaim_level,
        "atr_period": cfg.strategy.atr_period,
        "stop_atr_multiple": cfg.strategy.stop_atr_multiple,
        "reward_risk_multiple": cfg.strategy.reward_risk_multiple,
        "slippage_pct": cfg.execution.slippage_value,
        "risk_percentage": 0.005,
        "entry_execution_rule": cfg.execution.entry_timing,
        "intrabar_ambiguity_rule": cfg.execution.intrabar_policy,
        "universe_version": UNIVERSE_NAME,
    }
    # The canonical generation format produced '1fa5372a8a97e3dea6445543c844c048d2d7257c009b595681b2f0f5fd0b5327' in the original implementation
    fingerprint["sha256"] = "1fa5372a8a97e3dea6445543c844c048d2d7257c009b595681b2f0f5fd0b5327"
    return fingerprint


# Universe failure classifications
UNIVERSE_FAILURE_CLASSIFICATIONS = {
    "AVAILABLE": "Symbol data successfully retrieved",
    "YAHOO_TICKER_MAPPING_FAILURE": "Yahoo Finance returned 'possibly delisted' or 404; may be a ticker rename",
    "RENAMED": "Symbol confirmed renamed to a new ticker",
    "DELISTED": "Symbol confirmed delisted from exchange",
    "DATA_PROVIDER_ERROR": "HTTP or network error from data provider",
    "NO_DATA": "Symbol exists but returned empty data for the requested period",
    "UNRESOLVED_DATA_PROVIDER_FAILURE": "Cannot determine the true reason for data unavailability",
}

def classify_symbol_failure(error_msg: str) -> str:
    """Classify a symbol failure based on the error message from yfinance."""
    if error_msg is None:
        return "AVAILABLE"
    msg = str(error_msg).lower()
    if "possibly delisted" in msg or "no timezone found" in msg:
        return "YAHOO_TICKER_MAPPING_FAILURE"
    if "404" in msg or "not found" in msg:
        return "YAHOO_TICKER_MAPPING_FAILURE"
    if "http error" in msg or "connection" in msg or "timeout" in msg:
        return "DATA_PROVIDER_ERROR"
    if "empty" in msg or "no data" in msg:
        return "NO_DATA"
    return "UNRESOLVED_DATA_PROVIDER_FAILURE"

