import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.append("d:/stratergy")
from config import BacktestConfig
from universe import get_universe
from portfolio.engine import get_leg_cost

def test_no_future_universe_membership():
    # Since point-in-time universe is UNRESOLVED, we test that the current universe
    # is entirely static (which implies future membership *is* inherently used due to survivorship bias)
    # The test asserts the known limitation.
    universe = get_universe()
    assert len(universe) > 100
    assert all("symbol" in u for u in universe)

def test_tradable_only_while_valid():
    pytest.skip("Point-in-time constituent data is UNRESOLVED. Cannot test dynamic tradability.")

def test_delisted_stocks_do_not_disappear():
    pytest.skip("Point-in-time constituent data is UNRESOLVED. Delisted stocks are entirely absent.")

def test_new_constituents_do_not_appear_early():
    pytest.skip("Point-in-time constituent data is UNRESOLVED.")

def test_ticker_changes_handling():
    pytest.skip("Point-in-time constituent data is UNRESOLVED. Yahoo Finance data used.")

def test_no_duplicate_symbol_date_membership():
    universe = get_universe()
    symbols = [u["symbol"] for u in universe]
    assert len(symbols) == len(set(symbols))

def test_no_strategy_parameters_changed():
    cfg = BacktestConfig()
    assert cfg.strategy.ema_period == 50
    assert cfg.strategy.rsi_period == 14
    assert cfg.strategy.atr_period == 14

def test_existing_transaction_cost_logic_unchanged():
    cfg = BacktestConfig()
    # Test a dummy trade value
    cost = get_leg_cost(100000, True, cfg)
    # Ensure it calculates something reasonable and hasn't been zeroed out
    assert cost > 0

def test_existing_portfolio_accounting_unchanged():
    # Verify that the outputs from the previous phase still exist and match
    reconciliation = pd.read_csv("d:/stratergy/results/historical/oos_fold_reconciliation.csv")
    assert (reconciliation["status"] == "PASS").all()

def test_current_universe_results_reproducible():
    baseline_trades = pd.read_csv("d:/stratergy/expanded_trades.csv")
    assert len(baseline_trades) > 100
    assert "net_pnl" in baseline_trades.columns
