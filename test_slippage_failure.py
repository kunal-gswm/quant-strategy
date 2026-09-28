import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import sys
sys.path.append("d:/stratergy")
from run_forward_session import generate_milestones
from forward_engine import RESULTS_DIR

@pytest.fixture(autouse=True)
def clean_results():
    files = list(RESULTS_DIR.glob("milestone_*.md")) + [RESULTS_DIR / "forward_trades.csv"]
    for f in files:
        if f.exists():
            f.unlink()
    yield
    for f in files:
        if f.exists():
            f.unlink()

def create_mock_trades(n_trades, n_excessive, consecutive=False):
    # n_trades = 25
    # threshold > 0.10 round trip
    rows = []
    
    # generate pattern
    if consecutive:
        # put excessive trades at the end
        excessive_idx = list(range(n_trades - n_excessive, n_trades))
    else:
        # alternate them
        excessive_idx = [i * 2 for i in range(n_excessive)]
        
    for i in range(n_trades):
        if i in excessive_idx:
            # excessive (round trip > 0.10%)
            actual_entry = 100.06 # 0.06%
            actual_exit = 119.93 # 0.058%
        else:
            # normal (round trip <= 0.10%)
            actual_entry = 100.01
            actual_exit = 119.99
            
        rows.append({
            "exit_timestamp": "2026-10-01",
            "net_pnl": 10,
            "r_multiple": 0.5,
            "transaction_costs": 1,
            "planned_entry": 100,
            "actual_entry": actual_entry,
            "planned_stop": 90,
            "planned_target": 120,
            "actual_exit": actual_exit,
            "exit_reason": "TARGET",
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "forward_trades.csv", index=False)

def test_slippage_1_excessive_does_not_trigger():
    create_mock_trades(25, 1, True)
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_slippage_24_consecutive_does_not_trigger():
    create_mock_trades(25, 24, True)
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_slippage_25_consecutive_triggers():
    create_mock_trades(25, 25, True)
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: TRIGGERED" in content

def test_slippage_non_consecutive_does_not_trigger():
    create_mock_trades(25, 12, False) # 12 alternating
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_exactly_10_bps_does_not_count():
    # Exactly 0.10% total slip
    rows = [{
        "exit_timestamp": "2026-10-01",
        "net_pnl": 10,
        "r_multiple": 0.5,
        "transaction_costs": 1,
        "planned_entry": 100,
        "actual_entry": 100.05,
        "planned_stop": 90,
        "planned_target": 120,
        "actual_exit": 119.94, # target slip = (120-119.94)/120 = 0.06/120 = 0.05%
        "exit_reason": "TARGET",
    }] * 25
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "forward_trades.csv", index=False)
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content
    assert "Trades exceeding threshold: 0/25" in content

def test_open_cancelled_excluded():
    # Create 25 completed + 10 open/cancelled (no exit_timestamp)
    rows = []
    for _ in range(25):
        rows.append({
            "exit_timestamp": "2026-10-01",
            "net_pnl": 10,
            "r_multiple": 0.5,
            "transaction_costs": 1,
            "planned_entry": 100,
            "actual_entry": 100.01,
            "planned_stop": 90,
            "planned_target": 120,
            "actual_exit": 119.99,
            "exit_reason": "TARGET",
        })
    for _ in range(10):
        rows.append({
            "exit_timestamp": np.nan, # open
            "net_pnl": 0,
            "r_multiple": 0,
            "transaction_costs": 1,
            "planned_entry": 100,
            "actual_entry": 100.5, # Huge slip but open
            "planned_stop": 90,
            "planned_target": 120,
            "actual_exit": np.nan,
            "exit_reason": np.nan,
        })
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "forward_trades.csv", index=False)
    generate_milestones()
    with open(RESULTS_DIR / "milestone_25.md") as f:
        content = f.read()
    assert "Trades exceeding threshold: 0/25" in content # The huge slip was excluded

def test_strategy_config_unchanged():
    from forward_config import get_frozen_forward_config
    cfg = get_frozen_forward_config()
    assert cfg.execution.slippage_value == 0.05
