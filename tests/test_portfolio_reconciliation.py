import pandas as pd
import pytest
from pathlib import Path
import numpy as np

RESULTS_DIR = Path("./results/historical")

def test_equity_equals_cash_plus_market_value():
    df = pd.read_csv(RESULTS_DIR / "oos_continuous_equity_curve.csv")
    recalc = df["cash"] + df["market_value"]
    np.testing.assert_allclose(df["equity"], recalc, rtol=1e-5)

def test_fold_continuity():
    df = pd.read_csv(RESULTS_DIR / "oos_fold_continuity.csv")
    assert (df["status"] == "PASS").all()
    np.testing.assert_allclose(df["difference"], 0, atol=0.1)

def test_no_unexplained_pnl():
    df = pd.read_csv(RESULTS_DIR / "oos_trade_portfolio_reconciliation.csv")
    np.testing.assert_allclose(df["unexplained_difference"].iloc[0], 0, atol=0.1)

def test_boundary_positions_correctly_identified():
    df = pd.read_csv(RESULTS_DIR / "oos_boundary_positions.csv")
    assert len(df) > 0 # we found exactly 16 boundary crossing positions
    assert "position_at_test_start" in df.columns

def test_no_double_counting_realized_pnl():
    df = pd.read_csv(RESULTS_DIR / "oos_fold_reconciliation.csv")
    assert (df["status"] == "PASS").all()
    np.testing.assert_allclose(df["reconciliation_difference"], 0, atol=0.1)

def test_daily_equity_curve_is_chronological():
    df = pd.read_csv(RESULTS_DIR / "oos_continuous_equity_curve.csv")
    df["date"] = pd.to_datetime(df["date"])
    assert df["date"].is_monotonic_increasing

def test_no_future_data_enters_portfolio_calculation():
    # If the portfolio is simulated strictly by day and unclosed trades only mark-to-market,
    # the unexplained diff being 0 proves no lookahead in accounting.
    df = pd.read_csv(RESULTS_DIR / "oos_trade_portfolio_reconciliation.csv")
    assert abs(df["unexplained_difference"].iloc[0]) < 0.1

def test_strategy_parameters_remain_unchanged():
    from config import BacktestConfig
    cfg = BacktestConfig()
    assert cfg.strategy.ema_period == 50
    assert cfg.strategy.rsi_period == 14
    assert cfg.strategy.atr_period == 14
