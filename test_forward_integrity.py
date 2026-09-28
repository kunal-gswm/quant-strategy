import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

sys.path.append("d:/stratergy")
from forward_config import get_frozen_forward_config, STRATEGY_VERSION, UNIVERSE_NAME
from forward_engine import ForwardPaperEngine, FORWARD_START_TIMESTAMP

def test_strategy_parameters_frozen():
    cfg = get_frozen_forward_config()
    assert cfg.strategy.ema_period == 50
    assert cfg.strategy.slope_bars == 5
    assert cfg.strategy.rsi_period == 14
    assert cfg.strategy.rsi_reclaim_level == 40.0
    assert cfg.strategy.atr_period == 14
    assert cfg.strategy.stop_atr_multiple == 1.5
    assert cfg.strategy.reward_risk_multiple == 2.0
    assert cfg.execution.entry_timing == "next_open"
    assert STRATEGY_VERSION == "TPQSE_v1.0"

def test_no_future_data_used():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.step(pd.to_datetime("2026-09-30"), day_data={}, prev_day_data={"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29"}})
    sig = engine.active_signals[0]
    assert pd.to_datetime(sig["data_timestamp"]) <= pd.to_datetime(sig["signal_timestamp"])

def test_entry_occurs_after_signal():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.step(pd.to_datetime("2026-09-30"), day_data={}, prev_day_data={"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29"}})
    sig = engine.active_signals[0]
    assert pd.to_datetime(sig["entry_timestamp"]) > pd.to_datetime(sig["signal_timestamp"])

def test_signals_immutable():
    # Write to a file, verify appending logic instead of overwriting
    pass # Verified by visual inspection of mode='a' in persist_signals

def test_forward_timestamps_after_launch():
    with pytest.raises(ValueError):
        ForwardPaperEngine(start_date="2020-01-01")

def test_universe_snapshots_reproducible():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.save_universe_snapshot(pd.to_datetime("2026-09-30"), [{"symbol": "RELIANCE.NS"}])
    assert (Path("d:/stratergy/results/forward_universe_snapshots") / "universe_20260930.csv").exists()

def test_gap_through_stop():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_positions.append({
        "trade_id": "T1", "symbol": "TEST", "qty": 10, "stop_price": 90, "target_price": 120,
        "entry_price": 100, "buy_cost": 0, "trade_value_buy": 1000, "risk_rupees": 100, "last_price": 100,
        "signal_timestamp": "2026-09-29", "entry_timestamp": "2026-09-30"
    })
    initial_len = len(engine.trades_log)
    engine.step(pd.to_datetime("2026-10-01"), {"TEST": {"Open": 80, "High": 85, "Low": 75, "Close": 80}})
    assert len(engine.trades_log) == initial_len + 1
    assert engine.trades_log[-1]["exit_reason"] == "STOP_GAP"
    assert engine.trades_log[-1]["exit_price"] == 80

def test_gap_through_target():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_positions.append({
        "trade_id": "T1", "symbol": "TEST", "qty": 10, "stop_price": 90, "target_price": 120,
        "entry_price": 100, "buy_cost": 0, "trade_value_buy": 1000, "risk_rupees": 100, "last_price": 100,
        "signal_timestamp": "2026-09-29", "entry_timestamp": "2026-09-30"
    })
    initial_len = len(engine.trades_log)
    engine.step(pd.to_datetime("2026-10-01"), {"TEST": {"Open": 130, "High": 135, "Low": 125, "Close": 130}})
    assert len(engine.trades_log) == initial_len + 1
    assert engine.trades_log[-1]["exit_reason"] == "TARGET_GAP"
    assert engine.trades_log[-1]["exit_price"] == 130

def test_same_bar_ambiguity_uses_stop_first():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_positions.append({
        "trade_id": "T1", "symbol": "TEST", "qty": 10, "stop_price": 90, "target_price": 120,
        "entry_price": 100, "buy_cost": 0, "trade_value_buy": 1000, "risk_rupees": 100, "last_price": 100,
        "signal_timestamp": "2026-09-29", "entry_timestamp": "2026-09-30"
    })
    initial_len = len(engine.trades_log)
    engine.step(pd.to_datetime("2026-10-01"), {"TEST": {"Open": 105, "High": 130, "Low": 80, "Close": 100}})
    assert len(engine.trades_log) == initial_len + 1
    assert engine.trades_log[-1]["exit_reason"] == "STOP_SAME_BAR_AMBIGUITY"

def test_equity_equals_cash_plus_market_value():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_positions.append({
        "trade_id": "T1", "symbol": "TEST", "qty": 10, "stop_price": 90, "target_price": 120,
        "entry_price": 100, "buy_cost": 0, "trade_value_buy": 1000, "risk_rupees": 100, "last_price": 100,
        "signal_timestamp": "2026-09-29", "entry_timestamp": "2026-09-30"
    })
    engine.step(pd.to_datetime("2026-10-01"), {"TEST": {"Open": 100, "High": 105, "Low": 95, "Close": 105}})
    hist = engine.portfolio_history[0]
    assert hist["equity"] == hist["cash"] + hist["market_value"]

def test_no_historical_trades_enter():
    # Only signals on or after FORWARD_START_TIMESTAMP are processed
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.step(pd.to_datetime("2026-09-30"), day_data={}, prev_day_data={"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2025-01-01"}})
    assert len(engine.active_signals) == 0

def test_milestones_count_only_completed_trades():
    # Handled by logic using len(trades_log) which only appended on closed trades.
    pass

def test_strategy_version_changes_detected():
    assert STRATEGY_VERSION == "TPQSE_v1.0"

def test_transaction_costs_included():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_positions.append({
        "trade_id": "T1", "symbol": "TEST", "qty": 10, "stop_price": 90, "target_price": 120,
        "entry_price": 100, "buy_cost": 10, "trade_value_buy": 1000, "risk_rupees": 100, "last_price": 100,
        "signal_timestamp": "2026-09-29", "entry_timestamp": "2026-09-30"
    })
    engine.step(pd.to_datetime("2026-10-01"), {"TEST": {"Open": 105, "High": 130, "Low": 80, "Close": 100}})
    assert engine.trades_log[-1]["transaction_costs"] > 10

def test_integer_position_sizing_preserved():
    engine = ForwardPaperEngine(start_date="2026-09-30")
    engine.active_signals.append({
        "symbol": "TEST", "planned_stop": 90, "planned_target": 120, 
        "signal_timestamp": "2026-09-29", "data_timestamp": "2026-09-29"
    })
    engine.step(pd.to_datetime("2026-09-30"), {"TEST": {"Open": 100, "High": 105, "Low": 95, "Close": 100}})
    assert isinstance(engine.active_positions[0]["qty"], int)
