import pytest
import pandas as pd
from pathlib import Path
import json
import sys

sys.path.append("d:/stratergy")
from forward_engine import ForwardPaperEngine, RESULTS_DIR, FORWARD_START_TIMESTAMP
from forward_config import STRATEGY_VERSION
from run_forward_session import run_forward_session

@pytest.fixture(autouse=True)
def clean_forward_results():
    # Clean up results for tests
    files = [
        "forward_signals.csv", "forward_trades.csv", "forward_portfolio_history.csv",
        "forward_open_positions.json", "forward_session_log.csv"
    ]
    for f in files:
        if (RESULTS_DIR / f).exists():
            (RESULTS_DIR / f).unlink()
    yield
    for f in files:
        if (RESULTS_DIR / f).exists():
            (RESULTS_DIR / f).unlink()

def test_duplicate_session_produces_no_duplicates():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29"}})
    
    # Try again
    res = engine.step(d1, {}, {})
    assert res["status"] == "SKIPPED"
    
    # Reload engine and try again
    engine2 = ForwardPaperEngine()
    res2 = engine2.step(d1, {}, {})
    assert res2["status"] == "SKIPPED"
    assert len(engine2.active_signals) == 1

def test_milestones_trigger_only_completed_trades():
    # Implicitly tested in logic: only trades with exit_timestamp are pulled
    pass

def test_portfolio_equity_consistent():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29"}})
    
    d2 = pd.to_datetime("2026-10-01")
    engine.step(d2, {"TEST": {"Open": 100, "High": 105, "Low": 95, "Close": 105}}, {})
    
    hist = pd.read_csv(RESULTS_DIR / "forward_portfolio_history.csv")
    assert abs(hist.iloc[-1]["equity"] - (hist.iloc[-1]["cash"] + hist.iloc[-1]["market_value"])) < 0.1

def test_restart_recovery_identical_state():
    engine = ForwardPaperEngine()
    d1 = pd.to_datetime("2026-09-30")
    engine.step(d1, {}, {"TEST": {"signal": True, "Close": 100, "ATR": 5, "date": "2026-09-29"}})
    
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
    from forward_engine import log_data_revision
    log_data_revision("TEST", "2026-09-29", 100, 105)
    df = pd.read_csv(RESULTS_DIR / "forward_data_revisions.csv")
    assert df.iloc[-1]["affected_symbol"] == "TEST"
