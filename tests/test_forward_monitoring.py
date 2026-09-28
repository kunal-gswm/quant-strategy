import pytest
import pandas as pd
from pathlib import Path
import json
import sys

sys.path.append(".")
from forward.engine import ForwardPaperEngine, FORWARD_START_TIMESTAMP
from forward.config import STRATEGY_VERSION
from forward.session import run_forward_session


def test_duplicate_session_produces_no_duplicates():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29", "EMA": 95, "EMA_slope": 1.0, "RSI": 42}})

    res = engine.step(d1, {}, {})
    assert res["status"] == "SKIPPED"

    engine2 = ForwardPaperEngine()
    res2 = engine2.step(d1, {}, {})
    assert res2["status"] == "SKIPPED"
    assert len(engine2.active_signals) == 1

def test_milestones_trigger_only_completed_trades():
    pass

def test_portfolio_equity_consistent():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29", "EMA": 95, "EMA_slope": 1.0, "RSI": 42}})

    d2 = pd.to_datetime("2026-10-01")
    engine.step(d2, {"TEST": {"Open": 100, "High": 105, "Low": 95, "Close": 105}}, {})

    import forward.engine
    hist = pd.read_csv(forward.engine.RESULTS_DIR / "forward_portfolio_history.csv")
    assert abs(hist.iloc[-1]["equity"] - (hist.iloc[-1]["cash"] + hist.iloc[-1]["market_value"])) < 0.1

def test_restart_recovery_identical_state():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29", "EMA": 95, "EMA_slope": 1.0, "RSI": 42}})

    d2 = pd.to_datetime("2026-10-01")
    engine.step(d2, {"TEST": {"Open": 100, "High": 105, "Low": 95, "Close": 105}}, {})

    cash1 = engine.cash

    engine2 = ForwardPaperEngine()
    assert abs(engine2.cash - cash1) < 0.1
    assert len(engine2.active_positions) == 1
    assert engine2.active_positions[0]["symbol"] == "TEST"

def test_historical_trades_cannot_enter():
    engine = ForwardPaperEngine()
    res = engine.step(pd.to_datetime("2020-01-01"), {}, {})
    assert res["status"] == "SKIPPED"
    assert res["reason"] == "Before launch"

def test_strategy_version_locked():
    assert STRATEGY_VERSION == "TPQSE_v1.0"

def test_data_revisions_logged():
    from forward.engine import log_data_revision
    import forward.engine
    log_data_revision("TEST", "2026-09-29", 100, 105)
    df = pd.read_csv(forward.engine.RESULTS_DIR / "forward_data_revisions.csv")
    assert df.iloc[-1]["affected_symbol"] == "TEST"
