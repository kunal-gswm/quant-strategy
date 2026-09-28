import pytest
import pandas as pd
from pathlib import Path

RESULTS_DIR = Path("d:/stratergy/results/historical")

def test_training_trades_excluded_from_oos():
    integrity = pd.read_csv(RESULTS_DIR / "walk_forward_integrity.csv")
    assert integrity["overlap_count"].sum() == 0, "Test windows overlap with training periods!"
    assert (integrity["test_trades"] > 0).all(), "Some test folds have zero trades!"

def test_test_windows_do_not_overlap():
    integrity = pd.read_csv(RESULTS_DIR / "walk_forward_integrity.csv")
    test_starts = pd.to_datetime(integrity["test_start"])
    test_ends = pd.to_datetime(integrity["test_end"])
    # Check that for any fold i, test_start[i+1] > test_end[i]
    for i in range(len(integrity) - 1):
        assert test_starts.iloc[i+1] > test_ends.iloc[i], "Test windows overlap!"

def test_each_oos_trade_belongs_to_exactly_one_fold():
    test_trades = pd.read_csv(RESULTS_DIR / "walk_forward_test_trades.csv")
    # Group by fold and check
    folds = test_trades["fold"].unique()
    assert len(folds) == 5, "Not all 5 folds are present in test trades!"
    
    # Check that a single trade (symbol + signal_timestamp) only appears once
    duplicates = test_trades.duplicated(subset=["symbol", "signal_timestamp"])
    assert not duplicates.any(), "Duplicate trades found across folds!"

def test_full_baseline_not_used_as_oos():
    baseline = pd.read_csv("d:/stratergy/expanded_trades.csv")
    test_trades = pd.read_csv(RESULTS_DIR / "walk_forward_test_trades.csv")
    assert len(test_trades) < len(baseline), "Test trades are equal to baseline trades! Full baseline was used as OOS!"

def test_2025_reproduces_expected_test_window_result():
    test_trades = pd.read_csv(RESULTS_DIR / "walk_forward_test_trades.csv")
    trades_2025 = test_trades[test_trades["fold"] == 2025]
    
    # Old logic used signal_timestamp (28 trades). Correct strict exit logic gives 29.
    assert len(trades_2025) == 29, f"Expected 29 trades in 2025 (exit_timestamp), got {len(trades_2025)}"
    wins = len(trades_2025[trades_2025["net_pnl"] > 0])
    win_rate = wins / len(trades_2025)
    assert abs(win_rate - 0.4828) < 0.01, f"Expected ~48.28% win rate, got {win_rate:.2%}"
    
    net_pnl = trades_2025["net_pnl"].sum()
    assert abs(net_pnl - 9850) < 100, f"Expected ~9850 Net PnL, got {net_pnl}"

def test_portfolio_equity_uses_mark_to_market():
    # Load the portfolio metrics
    port = pd.read_csv(RESULTS_DIR / "walk_forward_oos_portfolio.csv")
    assert port["max_dd"].iloc[0] < 0.20, "Drawdown is excessively large (>20%), likely still using old cash accounting!"
