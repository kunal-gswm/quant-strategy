import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import sys
sys.path.append("d:/stratergy")
from forward.session import generate_milestones
import forward.engine


def create_mock_trades(results_dir, n_trades, n_excessive, consecutive=False):
    rows = []
    if consecutive:
        excessive_idx = list(range(n_trades - n_excessive, n_trades))
    else:
        excessive_idx = [i * 2 for i in range(n_excessive)]

    for i in range(n_trades):
        if i in excessive_idx:
            actual_entry = 100.06
            actual_exit = 119.93
        else:
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
    df.to_csv(results_dir / "forward_trades.csv", index=False)

def test_slippage_1_excessive_does_not_trigger():
    rd = forward.engine.RESULTS_DIR
    create_mock_trades(rd, 25, 1, True)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_slippage_24_consecutive_does_not_trigger():
    rd = forward.engine.RESULTS_DIR
    create_mock_trades(rd, 25, 24, True)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_slippage_25_consecutive_triggers():
    rd = forward.engine.RESULTS_DIR
    create_mock_trades(rd, 25, 25, True)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: TRIGGERED" in content

def test_slippage_non_consecutive_does_not_trigger():
    rd = forward.engine.RESULTS_DIR
    create_mock_trades(rd, 25, 12, False)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content

def test_exactly_10_bps_does_not_count():
    rd = forward.engine.RESULTS_DIR
    rows = [{
        "exit_timestamp": "2026-10-01",
        "net_pnl": 10,
        "r_multiple": 0.5,
        "transaction_costs": 1,
        "planned_entry": 100,
        "actual_entry": 100.05,
        "planned_stop": 90,
        "planned_target": 120,
        "actual_exit": 119.94,
        "exit_reason": "TARGET",
    }] * 25
    pd.DataFrame(rows).to_csv(rd / "forward_trades.csv", index=False)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "SLIPPAGE FAILURE: NOT TRIGGERED" in content
    assert "Trades exceeding threshold: 0/25" in content

def test_open_cancelled_excluded():
    rd = forward.engine.RESULTS_DIR
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
            "exit_timestamp": np.nan,
            "net_pnl": 0,
            "r_multiple": 0,
            "transaction_costs": 1,
            "planned_entry": 100,
            "actual_entry": 100.5,
            "planned_stop": 90,
            "planned_target": 120,
            "actual_exit": np.nan,
            "exit_reason": np.nan,
        })
    pd.DataFrame(rows).to_csv(rd / "forward_trades.csv", index=False)
    generate_milestones()
    with open(rd / "milestone_25.md") as f:
        content = f.read()
    assert "Trades exceeding threshold: 0/25" in content

def test_strategy_config_unchanged():
    from forward.config import get_frozen_forward_config
    cfg = get_frozen_forward_config()
    assert cfg.execution.slippage_value == 0.05
