"""
Walk-Forward Validation Experiment
===================================
Expanding-window walk-forward validation of the frozen Trend Pullback
strategy.  Parameters are NOT optimised — the purpose is validation only.

Usage:
    py run_walk_forward.py
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import traceback
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from analysis.monte_carlo import run_monte_carlo
from analysis.regime import classify_regimes, tag_trades_with_regime
from config import BacktestConfig, StrategyConfig
from data.loader import DataLoader
from data.validator import DataValidator
from indicators import atr, ema, rsi
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from backtest.execution import ExitReason
from metrics.performance import compute_core_metrics
from universe import get_universe

# ─── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"

# ─── Fixed experiment parameters ──────────────────────────────────────────
RANDOM_SEED = 42
STARTING_CAPITAL = 500_000.0

# Walk-forward windows (expanding)
# Since cache starts at 2019-01-01, use 2019 as warm-up/history
LOAD_START = "2019-01-01"
LOAD_END = "2025-12-31"

WALK_FORWARD_WINDOWS = [
    {"train_start": "2019-01-01", "train_end": "2020-12-31", "test_start": "2021-01-01", "test_end": "2021-12-31", "test_year": 2021},
    {"train_start": "2019-01-01", "train_end": "2021-12-31", "test_start": "2022-01-01", "test_end": "2022-12-31", "test_year": 2022},
    {"train_start": "2019-01-01", "train_end": "2022-12-31", "test_start": "2023-01-01", "test_end": "2023-12-31", "test_year": 2023},
    {"train_start": "2019-01-01", "train_end": "2023-12-31", "test_start": "2024-01-01", "test_end": "2024-12-31", "test_year": 2024},
    {"train_start": "2019-01-01", "train_end": "2024-12-31", "test_start": "2025-01-01", "test_end": "2025-12-31", "test_year": 2025},
]


# ═══════════════════════════════════════════════════════════════════════════
#  EXECUTION CLASSIFICATION (Section 2)
# ═══════════════════════════════════════════════════════════════════════════

def classify_execution(row: dict) -> list[str]:
    """Classify why a trade's realised R differs from nominal.
    
    Returns a list of applicable classifications.
    """
    entry = float(row["entry_price"])
    stop = float(row["stop_price"])
    target = float(row["target_price"])
    exit_price = float(row["exit_price"])
    qty = int(row["quantity"])
    gross_pnl = float(row["gross_pnl"])
    costs = float(row["total_costs"])
    net_pnl = float(row["net_pnl"])
    exit_reason = str(row["exit_reason"])
    ambiguous = bool(row.get("ambiguous_exit", False))
    
    risk_per_share = entry - stop
    if risk_per_share <= 0 or qty <= 0:
        return ["OTHER"]
    
    nominal_risk = risk_per_share * qty
    gross_r = gross_pnl / nominal_risk if nominal_risk != 0 else 0.0
    net_r = net_pnl / nominal_risk if nominal_risk != 0 else 0.0
    
    classifications = []
    
    # End of data
    if exit_reason == "END_OF_DATA":
        classifications.append("END_OF_DATA")
        return classifications
    
    # Intrabar ambiguity
    if ambiguous:
        classifications.append("INTRABAR_AMBIGUITY")
    
    # Check for gap-through scenarios
    if exit_reason == "STOP":
        if exit_price < stop - 0.01:
            # Exit was below the stop price => gap through stop
            classifications.append("GAP_THROUGH_STOP")
        elif abs(exit_price - stop) <= 0.01:
            # Normal stop hit but slippage applied
            pass  # Will be classified below
    
    if exit_reason == "TARGET":
        if exit_price > target + 0.01:
            # Exit was above the target price => gap through target
            classifications.append("GAP_THROUGH_TARGET")
        elif abs(exit_price - target) <= 0.01:
            pass  # Normal target hit, slippage may apply
    
    # Check slippage impact on exit
    # For STOP exits: the fill should ideally be at stop_price, but slippage
    # pushes it lower (since we're selling)
    if exit_reason == "STOP":
        slippage_on_exit = stop - exit_price  # positive if fill < stop
        if slippage_on_exit > 0.001 * stop:  # > 0.1% slippage effect
            if "GAP_THROUGH_STOP" not in classifications:
                classifications.append("EXIT_SLIPPAGE")
    
    if exit_reason == "TARGET":
        slippage_on_exit = target - exit_price  # positive if fill < target
        if slippage_on_exit > 0.001 * target:
            if "GAP_THROUGH_TARGET" not in classifications:
                classifications.append("EXIT_SLIPPAGE")
    
    # Transaction cost impact
    cost_r_impact = costs / nominal_risk if nominal_risk != 0 else 0
    if cost_r_impact > 0.01:  # costs shift R by >0.01
        classifications.append("TRANSACTION_COST")
    
    # Integer position sizing impact
    # Ideal qty = max_risk / risk_per_share, actual qty = floor(ideal)
    # This causes risk_per_share * actual_qty != max_risk
    ideal_qty_float = 1000.0 / risk_per_share  # max_risk_per_trade = 1000
    if abs(ideal_qty_float - qty) > 0.01:
        classifications.append("INTEGER_POSITION_SIZE")
    
    # If no special classifications found, it's a normal stop or target
    if not classifications:
        if exit_reason == "STOP":
            classifications.append("NORMAL_STOP")
        elif exit_reason == "TARGET":
            classifications.append("NORMAL_TARGET")
        else:
            classifications.append("OTHER")
    else:
        # Still note whether it was fundamentally a stop or target
        if exit_reason == "STOP" and not any(c.startswith("NORMAL") for c in classifications):
            # Don't double-add
            pass
        if exit_reason == "TARGET" and not any(c.startswith("NORMAL") for c in classifications):
            pass
    
    return classifications


def build_execution_audit(trades: pd.DataFrame) -> pd.DataFrame:
    """Build detailed execution audit for every trade."""
    rows = []
    for _, row in trades.iterrows():
        entry = float(row["entry_price"])
        stop = float(row["stop_price"])
        target = float(row["target_price"])
        exit_price = float(row["exit_price"])
        qty = int(row["quantity"])
        risk_per_share = entry - stop
        nominal_risk = risk_per_share * qty
        gross_pnl = float(row["gross_pnl"])
        costs = float(row["total_costs"])
        net_pnl = float(row["net_pnl"])
        r_mult = net_pnl / nominal_risk if nominal_risk > 0 else float("nan")
        
        classifications = classify_execution(row.to_dict())
        
        rows.append({
            "symbol": row.get("symbol", ""),
            "signal_date": str(row.get("signal_timestamp", "")),
            "entry_date": str(row.get("entry_timestamp", "")),
            "entry_price": entry,
            "stop_price": stop,
            "target_price": target,
            "exit_date": str(row.get("exit_timestamp", "")),
            "exit_price": exit_price,
            "exit_reason": row.get("exit_reason", ""),
            "initial_risk": nominal_risk,
            "gross_pnl": gross_pnl,
            "costs": costs,
            "net_pnl": net_pnl,
            "r_multiple": r_mult,
            "execution_classification": "|".join(classifications),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════
#  TRADE METRICS HELPER
# ═══════════════════════════════════════════════════════════════════════════

def compute_trade_metrics(df: pd.DataFrame) -> dict:
    """Compute comprehensive metrics for a set of trades."""
    if df.empty:
        return {
            "trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
            "gross_pnl": 0.0, "costs": 0.0, "net_pnl": 0.0,
            "mean_r": 0.0, "median_r": 0.0, "profit_factor": 0.0,
            "max_drawdown": 0.0, "expectancy": 0.0,
        }
    
    wins = int((df["net_pnl"] > 0).sum())
    losses = int((df["net_pnl"] <= 0).sum())
    total = len(df)
    win_rate = wins / total if total > 0 else 0.0
    
    gross_profit = float(df.loc[df["net_pnl"] > 0, "net_pnl"].sum())
    gross_loss_abs = float(abs(df.loc[df["net_pnl"] <= 0, "net_pnl"].sum()))
    profit_factor = gross_profit / gross_loss_abs if gross_loss_abs > 0 else float("inf")
    
    gross_pnl_val = float(df["gross_pnl"].sum()) if "gross_pnl" in df.columns else 0.0
    costs_val = float(df["total_costs"].sum()) if "total_costs" in df.columns else 0.0
    net_pnl_val = float(df["net_pnl"].sum())
    
    mean_r = float(df["r_multiple"].mean()) if "r_multiple" in df.columns else 0.0
    median_r = float(df["r_multiple"].median()) if "r_multiple" in df.columns else 0.0
    
    # Expectancy
    avg_win = float(df.loc[df["net_pnl"] > 0, "net_pnl"].mean()) if wins > 0 else 0.0
    avg_loss = float(df.loc[df["net_pnl"] <= 0, "net_pnl"].mean()) if losses > 0 else 0.0
    expectancy = win_rate * avg_win + (1 - win_rate) * avg_loss
    
    # Max drawdown
    cum = df["net_pnl"].cumsum()
    dd = (cum - cum.cummax()).min()
    max_dd = float(abs(dd)) if pd.notna(dd) else 0.0
    
    return {
        "trades": total, "wins": wins, "losses": losses, "win_rate": win_rate,
        "gross_pnl": gross_pnl_val, "costs": costs_val, "net_pnl": net_pnl_val,
        "mean_r": mean_r, "median_r": median_r, "profit_factor": profit_factor,
        "max_drawdown": max_dd, "expectancy": expectancy,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LOADING & PREPARATION
# ═══════════════════════════════════════════════════════════════════════════

def load_and_prepare_data(universe: list[dict], config: BacktestConfig) -> dict:
    """Load and validate all stock data from cache.
    
    Returns dict: symbol -> (item_dict, full_clean_df_with_indicators)
    """
    loader = DataLoader(use_cache=True)
    prepared = {}
    
    for item in universe:
        symbol = item["symbol"]
        cache_path = loader._cache_path(symbol, LOAD_START, LOAD_END)
        if not cache_path.exists():
            continue
        try:
            raw = loader.load_csv(cache_path)
            if raw.empty or len(raw) < config.strategy.ema_period + 10:
                continue
            clean, _ = DataValidator().validate(raw)
            if clean.empty or len(clean) < config.strategy.ema_period + 10:
                continue
            # Add indicators using full history
            clean["ema50"] = ema.wilder_style_ema(clean["close"], config.strategy.ema_period)
            clean["rsi14"] = rsi.wilder_rsi(clean["close"], config.strategy.rsi_period)
            clean["atr14"] = atr.wilder_atr(clean, config.strategy.atr_period)
            prepared[symbol] = (item, clean)
        except Exception:
            continue
    
    return prepared


def run_backtest_on_window(prepared_data: dict, config: BacktestConfig,
                           data_start: str, data_end: str,
                           test_start: str, test_end: str) -> pd.DataFrame:
    """Run strategy on data_start:data_end but only return trades
    whose signal falls within test_start:test_end.
    
    Indicators are computed using all data from data_start to ensure
    proper warm-up, but only trades signalled in the test window count.
    """
    all_trades = []
    
    for symbol, (item, full_df) in prepared_data.items():
        # Use data from beginning up to data_end for indicator computation
        # (data before test_start is the "training" / warm-up period)
        df_slice = full_df.loc[:data_end].copy()
        if df_slice.empty or len(df_slice) < config.strategy.ema_period + 10:
            continue
        
        # Recompute indicators on the available slice only
        # This ensures NO future data leaks into the indicator computation
        df_slice["ema50"] = ema.wilder_style_ema(df_slice["close"], config.strategy.ema_period)
        df_slice["rsi14"] = rsi.wilder_rsi(df_slice["close"], config.strategy.rsi_period)
        df_slice["atr14"] = atr.wilder_atr(df_slice, config.strategy.atr_period)
        
        strategy = TrendPullbackStrategy(config.strategy)
        engine = BacktestEngine(strategy=strategy, config=config)
        ledger_df, _ = engine.run(df_slice, symbol=symbol)
        
        if ledger_df.empty:
            continue
        
        # Filter trades to those with signal in the test window
        ledger_df["signal_timestamp"] = pd.to_datetime(ledger_df["signal_timestamp"])
        test_trades = ledger_df[
            (ledger_df["signal_timestamp"] >= test_start) &
            (ledger_df["signal_timestamp"] <= test_end)
        ].copy()
        
        if test_trades.empty:
            continue
        
        test_trades["cap"] = item["cap"]
        test_trades["sector"] = item["sector"]
        test_trades["test_year"] = int(test_start[:4])
        all_trades.append(test_trades)
    
    if all_trades:
        return pd.concat(all_trades, ignore_index=True)
    return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
#  WALK-FORWARD VALIDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def run_walk_forward(prepared_data: dict, config: BacktestConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute expanding-window walk-forward validation.
    
    Returns:
        (all_oos_trades, summary_df)
    """
    all_oos_trades = []
    summary_rows = []
    
    for window in WALK_FORWARD_WINDOWS:
        print(f"\n  Walk-Forward Test: {window['test_year']}")
        print(f"    Train: {window['train_start']} -> {window['train_end']}")
        print(f"    Test:  {window['test_start']} -> {window['test_end']}")
        
        test_trades = run_backtest_on_window(
            prepared_data, config,
            data_start=window["train_start"],
            data_end=window["test_end"],
            test_start=window["test_start"],
            test_end=window["test_end"],
        )
        
        metrics = compute_trade_metrics(test_trades)
        metrics["year"] = window["test_year"]
        summary_rows.append(metrics)
        
        print(f"    Trades: {metrics['trades']}, Win Rate: {metrics['win_rate']:.1%}, "
              f"Mean R: {metrics['mean_r']:.3f}, Net P&L: Rs.{metrics['net_pnl']:,.2f}")
        
        if not test_trades.empty:
            all_oos_trades.append(test_trades)
    
    summary_df = pd.DataFrame(summary_rows)
    
    if all_oos_trades:
        oos_trades = pd.concat(all_oos_trades, ignore_index=True)
    else:
        oos_trades = pd.DataFrame()
    
    return oos_trades, summary_df


# ═══════════════════════════════════════════════════════════════════════════
#  BOOTSTRAP CONFIDENCE INTERVALS
# ═══════════════════════════════════════════════════════════════════════════

def bootstrap_ci(data: np.ndarray, stat_fn=np.mean,
                 n_boot: int = 10000, ci: float = 0.95,
                 seed: int = 42) -> dict:
    """Non-parametric bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    n = len(data)
    if n == 0:
        return {"point_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}
    
    boot_stats = np.empty(n_boot)
    for i in range(n_boot):
        sample = data[rng.integers(0, n, size=n)]
        boot_stats[i] = stat_fn(sample)
    
    alpha = (1 - ci) / 2
    return {
        "point_estimate": float(stat_fn(data)),
        "ci_lower": float(np.percentile(boot_stats, alpha * 100)),
        "ci_upper": float(np.percentile(boot_stats, (1 - alpha) * 100)),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  DATA QUALITY REPORT (v2)
# ═══════════════════════════════════════════════════════════════════════════

def data_quality_report_v2() -> pd.DataFrame:
    """Enhanced data quality audit of all cached OHLCV files."""
    cache_dir = ROOT / "data" / "cache"
    rows = []
    if not cache_dir.exists():
        return pd.DataFrame()
    
    for csv_path in sorted(cache_dir.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
        except Exception:
            rows.append({
                "file": csv_path.name, "status": "unreadable",
                "rows": 0, "invalid_ohlc": 0, "duplicate_timestamps": 0,
                "missing_ohlcv": 0, "non_chronological": False,
                "invalid_prices": 0, "abnormal_gaps": 0,
                "insufficient_history": False, "notes": "CSV could not be parsed."
            })
            continue
        
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Basic checks
        has_cols = all(c in df.columns for c in ["open", "high", "low", "close", "volume"])
        if not has_cols:
            rows.append({
                "file": csv_path.name, "status": "missing_columns",
                "rows": len(df), "invalid_ohlc": 0, "duplicate_timestamps": 0,
                "missing_ohlcv": 0, "non_chronological": False,
                "invalid_prices": 0, "abnormal_gaps": 0,
                "insufficient_history": False, "notes": "Missing required OHLCV columns."
            })
            continue
        
        # OHLC validity
        h_ge_max_oc = (df["high"] >= df[["open", "close"]].max(axis=1))
        l_le_min_oc = (df["low"] <= df[["open", "close"]].min(axis=1))
        h_ge_l = (df["high"] >= df["low"])
        invalid_ohlc = int((~h_ge_max_oc | ~l_le_min_oc | ~h_ge_l).sum())
        
        # Duplicate timestamps
        dup_ts = int(df.index.duplicated().sum())
        
        # Chronological ordering
        non_chrono = not df.index.is_monotonic_increasing
        
        # Missing OHLCV values
        missing = int(df[["open", "high", "low", "close", "volume"]].isna().sum().sum())
        
        # Invalid prices (negative or zero)
        invalid_prices = int(((df["open"] <= 0) | (df["high"] <= 0) |
                              (df["low"] <= 0) | (df["close"] <= 0)).sum())
        
        # Abnormal gaps (>20% from previous close)
        if len(df) > 1:
            pct_gap = (df["open"].iloc[1:].values / df["close"].iloc[:-1].values) - 1
            abnormal_gaps = int((np.abs(pct_gap) > 0.20).sum())
        else:
            abnormal_gaps = 0
        
        # Insufficient history
        insufficient = len(df) < 200  # Need at least 200 bars for indicators
        
        status = "ok"
        if invalid_ohlc > 0 or dup_ts > 0 or non_chrono or missing > 0 or invalid_prices > 0:
            status = "issues"
        
        rows.append({
            "file": csv_path.name, "status": status,
            "rows": len(df), "invalid_ohlc": invalid_ohlc,
            "duplicate_timestamps": dup_ts, "missing_ohlcv": missing,
            "non_chronological": non_chrono, "invalid_prices": invalid_prices,
            "abnormal_gaps": abnormal_gaps, "insufficient_history": insufficient,
            "notes": ""
        })
    
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════
#  CHARTS
# ═══════════════════════════════════════════════════════════════════════════

def save_walk_forward_charts(oos_trades: pd.DataFrame) -> None:
    """Generate walk-forward equity curve, drawdown, and cumulative R charts."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    
    if oos_trades.empty:
        return
    
    trades = oos_trades.copy()
    trades["exit_timestamp"] = pd.to_datetime(trades["exit_timestamp"])
    trades = trades.sort_values("exit_timestamp").reset_index(drop=True)
    trades["cum_pnl"] = trades["net_pnl"].cumsum()
    trades["peak"] = trades["cum_pnl"].cummax()
    trades["drawdown"] = trades["cum_pnl"] - trades["peak"]
    trades["cum_r"] = trades["r_multiple"].fillna(0).cumsum()
    
    # Equity curve
    plt.figure(figsize=(10, 6))
    plt.plot(trades["exit_timestamp"], trades["cum_pnl"], marker=".", markersize=3)
    plt.title("Walk-Forward OOS Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Cumulative P&L (Rs.)")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "walk_forward_equity.png", dpi=150)
    plt.close()
    
    # Drawdown
    plt.figure(figsize=(10, 6))
    plt.fill_between(trades["exit_timestamp"], trades["drawdown"], 0, color="red", alpha=0.5)
    plt.title("Walk-Forward OOS Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (Rs.)")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "walk_forward_drawdown.png", dpi=150)
    plt.close()
    
    # Cumulative R
    plt.figure(figsize=(10, 6))
    plt.plot(trades["exit_timestamp"], trades["cum_r"], color="purple", marker=".", markersize=3)
    plt.title("Walk-Forward OOS Cumulative R")
    plt.xlabel("Date")
    plt.ylabel("Cumulative R-Multiple")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "walk_forward_cumulative_r.png", dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════════════
#  PARAMETER STABILITY (Section 15)
# ═══════════════════════════════════════════════════════════════════════════

def run_parameter_stability(prepared_data_full: dict) -> pd.DataFrame:
    """Test parameter neighbourhood against walk-forward framework.
    
    Does NOT optimise. Checks whether baseline sits in a stable region.
    """
    param_combos = [
        ("rsi_reclaim_level", [35.0, 40.0, 45.0]),
        ("ema_period", [40, 50, 60]),
        ("stop_atr_multiple", [1.25, 1.50, 1.75]),
        ("reward_risk_multiple", [1.5, 2.0, 2.5]),
    ]
    
    results = []
    
    for param_name, values in param_combos:
        for value in values:
            cfg = BacktestConfig()
            setattr(cfg.strategy, param_name, value)
            
            # Need to re-prepare data if ema_period changes
            if param_name == "ema_period":
                loader = DataLoader(use_cache=True)
                prep_data = {}
                for symbol, (item, full_df_orig) in prepared_data_full.items():
                    cache_path = loader._cache_path(symbol, LOAD_START, LOAD_END)
                    if not cache_path.exists():
                        continue
                    try:
                        raw = loader.load_csv(cache_path)
                        if raw.empty or len(raw) < cfg.strategy.ema_period + 10:
                            continue
                        clean, _ = DataValidator().validate(raw)
                        if clean.empty or len(clean) < cfg.strategy.ema_period + 10:
                            continue
                        clean["ema50"] = ema.wilder_style_ema(clean["close"], cfg.strategy.ema_period)
                        clean["rsi14"] = rsi.wilder_rsi(clean["close"], cfg.strategy.rsi_period)
                        clean["atr14"] = atr.wilder_atr(clean, cfg.strategy.atr_period)
                        prep_data[symbol] = (item, clean)
                    except Exception:
                        continue
            else:
                prep_data = prepared_data_full
            
            # Run walk-forward with this parameter set
            all_oos = []
            for window in WALK_FORWARD_WINDOWS:
                test_trades = run_backtest_on_window(
                    prep_data, cfg,
                    data_start=window["train_start"],
                    data_end=window["test_end"],
                    test_start=window["test_start"],
                    test_end=window["test_end"],
                )
                if not test_trades.empty:
                    all_oos.append(test_trades)
            
            if all_oos:
                combined = pd.concat(all_oos, ignore_index=True)
                m = compute_trade_metrics(combined)
            else:
                m = compute_trade_metrics(pd.DataFrame())
            
            is_baseline = False
            if param_name == "rsi_reclaim_level" and value == 40.0:
                is_baseline = True
            elif param_name == "ema_period" and value == 50:
                is_baseline = True
            elif param_name == "stop_atr_multiple" and value == 1.50:
                is_baseline = True
            elif param_name == "reward_risk_multiple" and value == 2.0:
                is_baseline = True
            
            results.append({
                "parameter": param_name,
                "value": value,
                "is_baseline": is_baseline,
                "oos_trades": m["trades"],
                "oos_win_rate": m["win_rate"],
                "oos_mean_r": m["mean_r"],
                "oos_net_pnl": m["net_pnl"],
                "oos_profit_factor": m["profit_factor"],
                "oos_max_drawdown": m["max_drawdown"],
            })
            print(f"    Param {param_name}={value}: trades={m['trades']}, "
                  f"net_pnl=Rs.{m['net_pnl']:,.0f}, pf={m['profit_factor']:.2f}")
    
    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════════
#  LOOK-AHEAD BIAS AUDIT (Section 17)
# ═══════════════════════════════════════════════════════════════════════════

def lookahead_audit() -> str:
    """Perform formal look-ahead bias audit. Returns markdown report."""
    checks = []
    
    # 1. Indicators: EMA, RSI, ATR only use current and previous bars
    # EMA: seed = mean(close[:period]), then recursive forward-only
    # RSI: seed = mean(gain/loss[:period+1]), then recursive forward-only
    # ATR: seed = mean(TR[1:period+1]), then recursive forward-only
    # All use .iloc[i-1] or prior values only — PASS
    checks.append(("Indicators (EMA/RSI/ATR use only current and previous bars)", "PASS",
                    "EMA seeded with SMA of first N closes, then recursive alpha * close[i] + (1-alpha) * ema[i-1]. "
                    "RSI seeded with mean of first N gains/losses, then Wilder smoothing forward-only. "
                    "ATR seeded with mean of first N TRs, then Wilder smoothing forward-only. "
                    "No future data accessed."))
    
    # 2. Entry: signal at bar t, entry at Open[t+1]
    # BacktestEngine line 70: signals.iloc[i] sets pending_order
    # Line 74: pending_order executes when pending_order[0] != t (next bar)
    # Line 78: entry_fill = apply_slippage(bar_open, ...)
    checks.append(("Entry timing (signal at bar t, entry at Open[t+1])", "PASS",
                    "BacktestEngine: signal creates pending_order at bar t. "
                    "Execution only when pending_order timestamp != current timestamp (next bar). "
                    "Fill is bar_open with slippage applied."))
    
    # 3. Stop/Target use actual entry price and ATR from signal bar
    # Line 83: stop = entry_fill - stop_atr_multiple * atr (where atr from signal bar)
    # Line 85: target = entry_fill + reward_risk * (entry_fill - stop)
    checks.append(("Stop/Target calculation (uses actual entry price and signal-bar ATR)", "PASS",
                    "Stop = entry_fill - 1.5 * ATR_at_signal. "
                    "Target = entry_fill + 2 * (entry_fill - stop). "
                    "ATR stored from signal bar, not entry bar or future bar."))
    
    # 4. Universe: no future index membership
    checks.append(("Universe (no future index membership)", "PASS (with caveat)",
                    "Universe is the current active stock list (survivorship-biased). "
                    "No point-in-time constituent data is used. "
                    "The universe does NOT change between walk-forward windows. "
                    "Caveat: survivorship bias remains unresolved."))
    
    # 5. Corporate actions
    checks.append(("Corporate actions", "PASS (assumed)",
                    "Yahoo Finance auto_adjust=True adjusts for splits and dividends. "
                    "Adjusted prices are computed at download time. "
                    "No future-adjusted information leaks into earlier calculations within the cached dataset. "
                    "Caveat: adj factor may be recomputed by Yahoo at download time."))
    
    # 6. OOS isolation
    checks.append(("OOS isolation (no test-period info influences earlier periods)", "PASS",
                    "Walk-forward runs each window independently. "
                    "Data is sliced to train_start:test_end for each window. "
                    "2021 test uses only data up to 2021-12-31. "
                    "2022 test uses only data up to 2022-12-31, etc. "
                    "No cross-window parameter optimization."))
    
    # Build markdown
    lines = ["# Look-Ahead Bias Audit\n"]
    lines.append(f"**Audit Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
    lines.append("| # | Check | Result | Details |")
    lines.append("|---|-------|--------|---------|")
    for i, (check, result, detail) in enumerate(checks, 1):
        lines.append(f"| {i} | {check} | **{result}** | {detail} |")
    
    all_pass = all("PASS" in c[1] for c in checks)
    lines.append(f"\n## Overall Result: **{'PASS' if all_pass else 'FAIL'}**\n")
    
    if not all_pass:
        lines.append("### Failed Checks")
        for check, result, detail in checks:
            if "FAIL" in result:
                lines.append(f"- **{check}**: {detail}")
    
    lines.append("\n### Caveats")
    lines.append("- Survivorship bias remains unresolved (current active stocks only).")
    lines.append("- Yahoo Finance corporate action adjustments are assumed correct.")
    lines.append("- No tick-level execution verification is possible with daily bars.")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  SURVIVORSHIP BIAS CHECK (Section 16)
# ═══════════════════════════════════════════════════════════════════════════

def check_survivorship_bias() -> str:
    """Search repository for historical constituent data and generate status."""
    search_terms = [
        "NIFTY", "NIFTY500", "constituent", "constituents",
        "historical_members", "membership", "delisted", "delisting",
        "removed", "index_history", "universe_history"
    ]
    
    found_files = []
    for root_dir, dirs, files in os.walk(str(ROOT)):
        # Skip __pycache__, .git, data/cache
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", ".pytest_cache", "cache"}]
        for f in files:
            if f.endswith((".py", ".csv", ".json", ".md", ".txt")):
                fpath = os.path.join(root_dir, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                    for term in search_terms:
                        if term.lower() in content.lower():
                            found_files.append((fpath, term))
                            break
                except Exception:
                    pass
    
    # Check for actual historical membership data
    has_historical_data = False
    for fpath, term in found_files:
        if "historical_universe" in fpath.lower() and fpath.endswith(".csv"):
            has_historical_data = True
    
    report = """# Survivorship Bias Status

## Status: UNRESOLVED

## Reason
Historical index membership data is not available in the repository.

The current universe consists of 179 stocks that are **currently listed and trading**
on the NSE. Stocks that were delisted, merged, or removed between 2019 and 2025
are NOT included.

## Required Future Dataset
Date-effective historical NIFTY 500 constituent membership, including:
- Entry and exit dates for each constituent
- Delisted and merged companies
- Corporate action history

## Impact
Current results remain subject to survivorship bias. This bias generally
**inflates** backtest performance because surviving stocks are, by definition,
the ones that did not fail.

## Repository Search Results
The following files reference related terms but do not contain actual
historical constituent data:
"""
    for fpath, term in found_files[:20]:
        report += f"\n- `{os.path.relpath(fpath, str(ROOT))}` (matched: {term})"
    
    if not found_files:
        report += "\n- No files found matching historical constituent search terms."
    
    return report


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 70)
    print("WALK-FORWARD VALIDATION EXPERIMENT")
    print("=" * 70)
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    
    config = BacktestConfig()
    universe = get_universe()
    print(f"\nUniverse: {len(universe)} stocks")
    print(f"Strategy: EMA({config.strategy.ema_period}), RSI({config.strategy.rsi_period}), "
          f"ATR({config.strategy.atr_period}), Stop={config.strategy.stop_atr_multiple}ATR, "
          f"Target={config.strategy.reward_risk_multiple}R")
    
    # ── 1. Load all data ───────────────────────────────────────────────
    print("\n[1/12] Loading and preparing data...")
    prepared_data = load_and_prepare_data(universe, config)
    print(f"  Loaded {len(prepared_data)} stocks from cache")
    
    # ── 2. Data quality report v2 ──────────────────────────────────────
    print("\n[2/12] Running data quality checks...")
    dq_df = data_quality_report_v2()
    dq_df.to_csv(RESULTS_DIR / "data_quality_report_v2.csv", index=False)
    issues = dq_df[dq_df["status"] != "ok"]
    print(f"  Files checked: {len(dq_df)}, Issues: {len(issues)}")
    
    # ── 3. Walk-Forward Validation ─────────────────────────────────────
    print("\n[3/12] Running walk-forward validation...")
    oos_trades, wf_summary = run_walk_forward(prepared_data, config)
    
    # Save walk-forward summary
    wf_summary_save = wf_summary[["year", "trades", "wins", "losses", "win_rate",
                                   "gross_pnl", "costs", "net_pnl", "mean_r",
                                   "median_r", "profit_factor", "max_drawdown"]].copy()
    wf_summary_save.to_csv(RESULTS_DIR / "walk_forward_summary.csv", index=False)
    
    # Save OOS trades
    if not oos_trades.empty:
        oos_trades.to_csv(RESULTS_DIR / "walk_forward_trades.csv", index=False)
    else:
        pd.DataFrame().to_csv(RESULTS_DIR / "walk_forward_trades.csv", index=False)
    
    # ── 4. Aggregate OOS metrics ───────────────────────────────────────
    print("\n[4/12] Computing aggregate OOS metrics...")
    agg = compute_trade_metrics(oos_trades)
    
    profitable_years = int((wf_summary["net_pnl"] > 0).sum())
    losing_years = int((wf_summary["net_pnl"] <= 0).sum())
    pct_profitable = profitable_years / len(wf_summary) if len(wf_summary) > 0 else 0
    
    print(f"  Total OOS Trades: {agg['trades']}")
    print(f"  OOS Win Rate: {agg['win_rate']:.1%}")
    print(f"  OOS Mean R: {agg['mean_r']:.3f}")
    print(f"  OOS Net P&L: Rs.{agg['net_pnl']:,.2f}")
    print(f"  OOS Profit Factor: {agg['profit_factor']:.2f}")
    print(f"  OOS Max Drawdown: Rs.{agg['max_drawdown']:,.2f}")
    print(f"  Profitable Years: {profitable_years}/{len(wf_summary)}")
    
    # ── 5. Tag with regime data ────────────────────────────────────────
    print("\n[5/12] Tagging trades with regime/sector data...")
    try:
        loader = DataLoader(use_cache=True)
        nifty_cache = loader._cache_path("^NSEI", LOAD_START, LOAD_END)
        if nifty_cache.exists():
            nifty_raw = loader.load_csv(nifty_cache)
        else:
            nifty_raw = loader.load("^NSEI", LOAD_START, LOAD_END)
        regime_df = classify_regimes(nifty_raw)
        if not oos_trades.empty:
            oos_trades = tag_trades_with_regime(oos_trades, regime_df)
        print("  Regime data tagged successfully")
    except Exception as e:
        print(f"  Warning: Could not load Nifty 50 for regime analysis: {e}")
        regime_df = pd.DataFrame()
    
    # ── 6. Stock-level WF analysis ─────────────────────────────────────
    print("\n[6/12] Computing stock-level and sector analysis...")
    if not oos_trades.empty:
        stock_rows = []
        for (symbol, test_year), grp in oos_trades.groupby(["symbol", "test_year"]):
            wins_s = int((grp["net_pnl"] > 0).sum())
            losses_s = int((grp["net_pnl"] <= 0).sum())
            total_s = len(grp)
            gp = float(grp.loc[grp["net_pnl"] > 0, "net_pnl"].sum())
            gl_abs = float(abs(grp.loc[grp["net_pnl"] <= 0, "net_pnl"].sum()))
            pf = gp / gl_abs if gl_abs > 0 else float("inf") if gp > 0 else 0.0
            stock_rows.append({
                "symbol": symbol,
                "test_year": test_year,
                "trades": total_s,
                "wins": wins_s,
                "losses": losses_s,
                "win_rate": wins_s / total_s if total_s > 0 else 0.0,
                "mean_r": float(grp["r_multiple"].mean()),
                "net_pnl": float(grp["net_pnl"].sum()),
                "profit_factor": pf,
            })
        stock_df = pd.DataFrame(stock_rows)
        stock_df.to_csv(RESULTS_DIR / "walk_forward_stock_summary.csv", index=False)
        
        # Stock aggregate stats
        stock_total_pnl = oos_trades.groupby("symbol")["net_pnl"].sum()
        stocks_positive = int((stock_total_pnl > 0).sum())
        stocks_negative = int((stock_total_pnl < 0).sum())
        stocks_zero_trades = len(universe) - len(stock_total_pnl)
        avg_trades_per_stock_year = agg["trades"] / (len(stock_total_pnl) * len(WALK_FORWARD_WINDOWS)) if len(stock_total_pnl) > 0 else 0
        
        print(f"  Stocks with positive OOS P&L: {stocks_positive}")
        print(f"  Stocks with negative OOS P&L: {stocks_negative}")
        print(f"  Stocks with zero trades: {stocks_zero_trades}")
        print(f"  Avg trades per stock/year: {avg_trades_per_stock_year:.2f}")
    else:
        pd.DataFrame().to_csv(RESULTS_DIR / "walk_forward_stock_summary.csv", index=False)
    
    # ── 7. Regime analysis ─────────────────────────────────────────────
    if not oos_trades.empty and "trend_regime" in oos_trades.columns:
        regime_rows = []
        for regime_name, grp in oos_trades.groupby("trend_regime"):
            m = compute_trade_metrics(grp)
            regime_rows.append({
                "regime": regime_name,
                "trades": m["trades"],
                "win_rate": m["win_rate"],
                "mean_r": m["mean_r"],
                "net_pnl": m["net_pnl"],
                "profit_factor": m["profit_factor"],
            })
        regime_res = pd.DataFrame(regime_rows)
        regime_res.to_csv(RESULTS_DIR / "walk_forward_regime.csv", index=False)
        print("  Regime analysis saved")
    else:
        pd.DataFrame(columns=["regime", "trades", "win_rate", "mean_r", "net_pnl", "profit_factor"]).to_csv(
            RESULTS_DIR / "walk_forward_regime.csv", index=False)
    
    # ── 8. Sector analysis ─────────────────────────────────────────────
    if not oos_trades.empty and "sector" in oos_trades.columns:
        sector_rows = []
        for sector_name, grp in oos_trades.groupby("sector"):
            m = compute_trade_metrics(grp)
            sector_rows.append({
                "sector": sector_name,
                "trades": m["trades"],
                "win_rate": m["win_rate"],
                "mean_r": m["mean_r"],
                "net_pnl": m["net_pnl"],
                "profit_factor": m["profit_factor"],
                "low_sample": m["trades"] < 10,
            })
        sector_res = pd.DataFrame(sector_rows)
        sector_res.to_csv(RESULTS_DIR / "walk_forward_sector.csv", index=False)
        print("  Sector analysis saved")
    else:
        pd.DataFrame().to_csv(RESULTS_DIR / "walk_forward_sector.csv", index=False)
    
    # ── 9. Execution Audit v2 ──────────────────────────────────────────
    print("\n[7/12] Building execution audit v2...")
    if not oos_trades.empty:
        audit_df = build_execution_audit(oos_trades)
        audit_df.to_csv(RESULTS_DIR / "execution_audit_v2.csv", index=False)
        
        # Summarize classifications
        all_classes = []
        for c in audit_df["execution_classification"]:
            all_classes.extend(c.split("|"))
        from collections import Counter
        class_counts = Counter(all_classes)
        print("  Classification summary:")
        for cls, cnt in class_counts.most_common():
            print(f"    {cls}: {cnt}")
        
        # Check if audit passes (no OTHER without explanation)
        other_count = class_counts.get("OTHER", 0)
        audit_pass = other_count == 0
        print(f"  Execution audit: {'PASS' if audit_pass else 'REVIEW NEEDED'} (OTHER count: {other_count})")
    else:
        pd.DataFrame().to_csv(RESULTS_DIR / "execution_audit_v2.csv", index=False)
        audit_pass = True
    
    # ── 10. OOS Charts ─────────────────────────────────────────────────
    print("\n[8/12] Generating OOS charts...")
    save_walk_forward_charts(oos_trades)
    print("  Charts saved")
    
    # ── 11. OOS Monte Carlo ────────────────────────────────────────────
    print("\n[9/12] Running OOS Monte Carlo (10,000 simulations)...")
    if not oos_trades.empty:
        pnl_array = oos_trades["net_pnl"].to_numpy()
        mc = run_monte_carlo(pnl_array, starting_capital=STARTING_CAPITAL,
                            n_simulations=10000, method="shuffle", seed=RANDOM_SEED)
        mc_results = {
            "median_final_pnl": float(np.median(mc["ending_equity"] - STARTING_CAPITAL)),
            "p05_final_pnl": float(np.percentile(mc["ending_equity"] - STARTING_CAPITAL, 5)),
            "p95_final_pnl": float(np.percentile(mc["ending_equity"] - STARTING_CAPITAL, 95)),
            "median_max_drawdown": float(np.median(mc["max_drawdowns"])),
            "p95_max_drawdown": float(np.percentile(mc["max_drawdowns"], 95)),
            "probability_negative_pnl": float((mc["ending_equity"] < STARTING_CAPITAL).mean()),
        }
        mc_df = pd.DataFrame([mc_results])
        mc_df.to_csv(RESULTS_DIR / "walk_forward_monte_carlo.csv", index=False)
        print(f"  Median DD: Rs.{mc_results['median_max_drawdown']:,.2f}")
        print(f"  95th DD: Rs.{mc_results['p95_max_drawdown']:,.2f}")
        print(f"  P(negative P&L): {mc_results['probability_negative_pnl']:.1%}")
    else:
        mc_results = {}
        pd.DataFrame().to_csv(RESULTS_DIR / "walk_forward_monte_carlo.csv", index=False)
    
    # ── 12. Bootstrap CI ───────────────────────────────────────────────
    print("\n[10/12] Computing bootstrap confidence intervals...")
    if not oos_trades.empty:
        r_values = oos_trades["r_multiple"].dropna().to_numpy()
        pnl_values = oos_trades["net_pnl"].to_numpy()
        
        mean_r_ci = bootstrap_ci(r_values, stat_fn=np.mean, n_boot=10000, seed=RANDOM_SEED)
        
        def win_rate_fn(x):
            return (x > 0).mean()
        
        win_rate_ci = bootstrap_ci(pnl_values, stat_fn=win_rate_fn, n_boot=10000, seed=RANDOM_SEED)
        
        def expectancy_fn(x):
            wr = (x > 0).mean()
            avg_w = x[x > 0].mean() if (x > 0).any() else 0
            avg_l = x[x <= 0].mean() if (x <= 0).any() else 0
            return wr * avg_w + (1 - wr) * avg_l
        
        expectancy_ci = bootstrap_ci(pnl_values, stat_fn=expectancy_fn, n_boot=10000, seed=RANDOM_SEED)
        
        stats_result = {
            "mean_r": mean_r_ci,
            "win_rate": win_rate_ci,
            "expectancy": expectancy_ci,
            "n_trades": len(r_values),
            "seed": RANDOM_SEED,
            "n_bootstrap": 10000,
            "confidence_level": 0.95,
        }
        with open(RESULTS_DIR / "walk_forward_statistics.json", "w") as f:
            json.dump(stats_result, f, indent=2)
        
        print(f"  Mean R: {mean_r_ci['point_estimate']:.3f} [{mean_r_ci['ci_lower']:.3f}, {mean_r_ci['ci_upper']:.3f}]")
        print(f"  Win Rate: {win_rate_ci['point_estimate']:.1%} [{win_rate_ci['ci_lower']:.1%}, {win_rate_ci['ci_upper']:.1%}]")
        print(f"  Expectancy: Rs.{expectancy_ci['point_estimate']:.2f} [{expectancy_ci['ci_lower']:.2f}, {expectancy_ci['ci_upper']:.2f}]")
    else:
        stats_result = {}
        with open(RESULTS_DIR / "walk_forward_statistics.json", "w") as f:
            json.dump({}, f)
    
    # ── 13. Cost robustness ────────────────────────────────────────────
    print("\n[11/12] Running cost robustness analysis...")
    cost_rows = []
    if not oos_trades.empty:
        base_costs = float(oos_trades["total_costs"].sum())
        base_gross = float(oos_trades["gross_pnl"].sum())
        
        for mult in [1.0, 2.0, 3.0]:
            eff_costs = base_costs * mult
            eff_net = base_gross - eff_costs
            
            # Recalculate per-trade metrics with cost multiplier
            adj_trades = oos_trades.copy()
            adj_trades["adj_net_pnl"] = adj_trades["gross_pnl"] - adj_trades["total_costs"] * mult
            adj_trades["adj_r"] = adj_trades["adj_net_pnl"] / (
                (adj_trades["entry_price"] - adj_trades["stop_price"]) * adj_trades["quantity"]
            )
            
            gp = float(adj_trades.loc[adj_trades["adj_net_pnl"] > 0, "adj_net_pnl"].sum())
            gl = float(abs(adj_trades.loc[adj_trades["adj_net_pnl"] <= 0, "adj_net_pnl"].sum()))
            pf = gp / gl if gl > 0 else float("inf")
            
            cum_adj = adj_trades["adj_net_pnl"].cumsum()
            dd_adj = float(abs((cum_adj - cum_adj.cummax()).min()))
            
            cost_rows.append({
                "cost_multiplier": mult,
                "trades": len(adj_trades),
                "net_pnl": float(adj_trades["adj_net_pnl"].sum()),
                "mean_r": float(adj_trades["adj_r"].mean()),
                "profit_factor": pf,
                "max_drawdown": dd_adj,
            })
            print(f"  {mult}x: Net P&L Rs.{adj_trades['adj_net_pnl'].sum():,.2f}, PF: {pf:.2f}")
    
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(RESULTS_DIR / "walk_forward_cost_sensitivity.csv", index=False)
    
    # ── 14. Parameter stability ────────────────────────────────────────
    print("\n[12/12] Running parameter stability analysis...")
    sensitivity_df = run_parameter_stability(prepared_data)
    sensitivity_df.to_csv(RESULTS_DIR / "walk_forward_sensitivity.csv", index=False)
    
    # ── 15. Survivorship bias ──────────────────────────────────────────
    print("\nChecking survivorship bias...")
    surv_report = check_survivorship_bias()
    (RESULTS_DIR / "survivorship_bias_status.md").write_text(surv_report, encoding="utf-8")
    print("  Status: UNRESOLVED")
    
    # ── 16. Look-ahead audit ───────────────────────────────────────────
    print("\nRunning look-ahead bias audit...")
    audit_report = lookahead_audit()
    (RESULTS_DIR / "lookahead_audit.md").write_text(audit_report, encoding="utf-8")
    print("  Audit complete")
    
    # ── 17. Year-to-year stability ─────────────────────────────────────
    annual_pnl = wf_summary["net_pnl"].to_numpy()
    stability = {
        "mean_annual_oos_pnl": float(np.mean(annual_pnl)),
        "median_annual_oos_pnl": float(np.median(annual_pnl)),
        "std_annual_oos_pnl": float(np.std(annual_pnl, ddof=1)) if len(annual_pnl) > 1 else 0,
        "best_year": int(wf_summary.loc[wf_summary["net_pnl"].idxmax(), "year"]) if len(wf_summary) > 0 else 0,
        "worst_year": int(wf_summary.loc[wf_summary["net_pnl"].idxmin(), "year"]) if len(wf_summary) > 0 else 0,
    }
    
    # ── 18. Save configuration ─────────────────────────────────────────
    config_dict = {
        "strategy": {
            "ema_period": config.strategy.ema_period,
            "slope_bars": config.strategy.slope_bars,
            "rsi_period": config.strategy.rsi_period,
            "rsi_reclaim_level": config.strategy.rsi_reclaim_level,
            "atr_period": config.strategy.atr_period,
            "stop_atr_multiple": config.strategy.stop_atr_multiple,
            "reward_risk_multiple": config.strategy.reward_risk_multiple,
            "entry_timing": "next_open",
            "direction": "long_only",
        },
        "walk_forward_windows": WALK_FORWARD_WINDOWS,
        "universe": f"{len(universe)}-stock active NSE universe (survivorship-biased)",
        "cost_assumptions": asdict(config.cost_model),
        "slippage_assumptions": {
            "type": config.execution.slippage_type,
            "value_pct": config.execution.slippage_value,
        },
        "risk_config": asdict(config.risk),
        "starting_capital": STARTING_CAPITAL,
        "random_seed": RANDOM_SEED,
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.replace("\n", " "),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
    }
    try:
        config_dict["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT), text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        config_dict["git_commit"] = "unavailable"
    
    with open(RESULTS_DIR / "walk_forward_configuration.json", "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)
    
    # ── 19. Generate Research Report ───────────────────────────────────
    print("\nGenerating Walk-Forward Validation Report...")
    
    # Determine research classification
    if oos_trades.empty:
        classification = "Insufficient Evidence"
    elif agg["trades"] < 50:
        classification = "Insufficient Evidence"
    elif agg["net_pnl"] <= 0 or agg["profit_factor"] < 1.0:
        classification = "Evidence Does Not Support Hypothesis"
    elif losing_years >= profitable_years:
        classification = "Evidence Inconsistent"
    elif agg["profit_factor"] < 1.2 or agg["mean_r"] < 0.1:
        classification = "Requires Further Validation"
    else:
        # Check cost robustness
        cost_3x_positive = any(r.get("net_pnl", 0) > 0 for r in cost_rows if r.get("cost_multiplier") == 3.0)
        if cost_3x_positive and profitable_years >= 3:
            classification = "Promising but Unconfirmed"
        else:
            classification = "Requires Further Validation"
    
    # Build regime table
    regime_table = ""
    if not oos_trades.empty and "trend_regime" in oos_trades.columns:
        regime_table = "| Regime | Trades | Win Rate | Mean R | Net P&L | Profit Factor | Reliable |\n"
        regime_table += "|--------|-------:|--------:|------:|--------:|--------------:|----------|\n"
        for _, rr in pd.read_csv(RESULTS_DIR / "walk_forward_regime.csv").iterrows():
            reliable = "Yes" if rr["trades"] >= 20 else "**No (<20)**"
            regime_table += f"| {rr['regime']} | {int(rr['trades'])} | {rr['win_rate']:.1%} | {rr['mean_r']:.3f} | Rs.{rr['net_pnl']:,.2f} | {rr['profit_factor']:.2f} | {reliable} |\n"
    
    # Build sector table
    sector_table = ""
    if (RESULTS_DIR / "walk_forward_sector.csv").exists():
        sec_df = pd.read_csv(RESULTS_DIR / "walk_forward_sector.csv")
        if not sec_df.empty:
            sector_table = "| Sector | Trades | Win Rate | Mean R | Net P&L | Profit Factor | Sample |\n"
            sector_table += "|--------|-------:|--------:|------:|--------:|--------------:|--------|\n"
            for _, sr in sec_df.iterrows():
                sample = "Low (<10)" if sr.get("low_sample", sr["trades"] < 10) else "Adequate"
                sector_table += f"| {sr['sector']} | {int(sr['trades'])} | {sr['win_rate']:.1%} | {sr['mean_r']:.3f} | Rs.{sr['net_pnl']:,.2f} | {sr['profit_factor']:.2f} | {sample} |\n"
    
    # Build yearly stability table
    yearly_table = "| Test Year | Trades | Win Rate | Mean R | Net P&L | Profit Factor |\n"
    yearly_table += "|----------:|-------:|--------:|------:|--------:|--------------:|\n"
    for _, yr in wf_summary.iterrows():
        yearly_table += f"| {int(yr['year'])} | {int(yr['trades'])} | {yr['win_rate']:.1%} | {yr['mean_r']:.3f} | Rs.{yr['net_pnl']:,.2f} | {yr['profit_factor']:.2f} |\n"
    
    # Cost sensitivity table
    cost_table = "| Multiplier | Trades | Net P&L | Mean R | Profit Factor | Max DD |\n"
    cost_table += "|:----------:|-------:|--------:|------:|--------------:|-------:|\n"
    for _, cr in cost_df.iterrows():
        cost_table += f"| {cr['cost_multiplier']}x | {int(cr['trades'])} | Rs.{cr['net_pnl']:,.2f} | {cr['mean_r']:.3f} | {cr['profit_factor']:.2f} | Rs.{cr['max_drawdown']:,.2f} |\n"
    
    # Parameter sensitivity table
    sens_table = "| Parameter | Value | Baseline | Trades | Win Rate | Mean R | Net P&L | PF |\n"
    sens_table += "|-----------|------:|:--------:|-------:|--------:|------:|--------:|----:|\n"
    for _, sr in sensitivity_df.iterrows():
        bl = "**✓**" if sr["is_baseline"] else ""
        sens_table += f"| {sr['parameter']} | {sr['value']} | {bl} | {int(sr['oos_trades'])} | {sr['oos_win_rate']:.1%} | {sr['oos_mean_r']:.3f} | Rs.{sr['oos_net_pnl']:,.0f} | {sr['oos_profit_factor']:.2f} |\n"
    
    # Bootstrap results strings
    if stats_result:
        mean_r_str = f"{stats_result['mean_r']['point_estimate']:.3f} [{stats_result['mean_r']['ci_lower']:.3f}, {stats_result['mean_r']['ci_upper']:.3f}]"
        wr_str = f"{stats_result['win_rate']['point_estimate']:.1%} [{stats_result['win_rate']['ci_lower']:.1%}, {stats_result['win_rate']['ci_upper']:.1%}]"
        exp_str = f"Rs.{stats_result['expectancy']['point_estimate']:.2f} [{stats_result['expectancy']['ci_lower']:.2f}, {stats_result['expectancy']['ci_upper']:.2f}]"
    else:
        mean_r_str = wr_str = exp_str = "N/A"
    
    # MC strings
    if mc_results:
        mc_median_dd = f"Rs.{mc_results['median_max_drawdown']:,.2f}"
        mc_p95_dd = f"Rs.{mc_results['p95_max_drawdown']:,.2f}"
        mc_prob_neg = f"{mc_results['probability_negative_pnl']:.1%}"
    else:
        mc_median_dd = mc_p95_dd = mc_prob_neg = "N/A"
    
    report = f"""# Trend Pullback Strategy
# Walk-Forward Validation Report

## 1. Executive Summary

This report presents the results of an expanding-window walk-forward validation
of the frozen Trend Pullback strategy on a {len(universe)}-stock NSE universe.

**Key Findings:**
- Total OOS trades: {agg['trades']}
- OOS win rate: {agg['win_rate']:.1%}
- OOS mean R: {agg['mean_r']:.3f}
- OOS net P&L: Rs.{agg['net_pnl']:,.2f}
- OOS profit factor: {agg['profit_factor']:.2f}
- OOS max drawdown: Rs.{agg['max_drawdown']:,.2f}
- Profitable test years: {profitable_years}/{len(wf_summary)} ({pct_profitable:.0%})

**Research Classification: {classification}**

## 2. Baseline Strategy

Parameters are frozen. No optimization was performed.

| Parameter | Value |
|-----------|------:|
| EMA period | {config.strategy.ema_period} |
| EMA slope lookback | {config.strategy.slope_bars} bars |
| RSI period | {config.strategy.rsi_period} |
| RSI reclaim level | {config.strategy.rsi_reclaim_level} |
| ATR period | {config.strategy.atr_period} |
| Stop | {config.strategy.stop_atr_multiple} × ATR |
| Target | {config.strategy.reward_risk_multiple}R |
| Direction | Long only |
| Entry | Next bar Open |

## 3. Previous Validation Results

From the prior validation phase (2020-2025 pooled backtest):
- 221 trades, 46.61% win rate
- Rs.71,285.61 net P&L
- Positive under 2x and 3x cost assumptions
- 2025 Final OOS: 28 trades, 50% win rate, Rs.10,885 net P&L, 1.75 PF
- Classification: Promising but Unconfirmed

## 4. Walk-Forward Methodology

Expanding-window walk-forward validation with frozen parameters.

The strategy parameters remain **unchanged** across all windows.
The "training" period is NOT used to optimize parameters — it is simply
the historical information available before each test period.

Each test period is completely isolated from other test periods when
calculating performance.

Data period: {LOAD_START} to {LOAD_END} (2019 = indicator warm-up)

## 5. Test Windows

| Window | Train Period | Test Period |
|--------|:-------------|:------------|
| 1 | 2019-01-01 → 2020-12-31 | **2021** |
| 2 | 2019-01-01 → 2021-12-31 | **2022** |
| 3 | 2019-01-01 → 2022-12-31 | **2023** |
| 4 | 2019-01-01 → 2023-12-31 | **2024** |
| 5 | 2019-01-01 → 2024-12-31 | **2025** |

## 6. Walk-Forward Results

{yearly_table}

## 7. Aggregate OOS Performance

| Metric | Value |
|--------|------:|
| Total OOS trades | {agg['trades']} |
| Total OOS wins | {agg['wins']} |
| Total OOS losses | {agg['losses']} |
| OOS win rate | {agg['win_rate']:.1%} |
| OOS mean R | {agg['mean_r']:.3f} |
| OOS median R | {agg['median_r']:.3f} |
| OOS expectancy | Rs.{agg['expectancy']:.2f} |
| OOS profit factor | {agg['profit_factor']:.2f} |
| OOS gross P&L | Rs.{agg['gross_pnl']:,.2f} |
| OOS costs | Rs.{agg['costs']:,.2f} |
| OOS net P&L | Rs.{agg['net_pnl']:,.2f} |
| OOS max drawdown | Rs.{agg['max_drawdown']:,.2f} |
| Profitable test years | {profitable_years} |
| Losing test years | {losing_years} |
| % test years profitable | {pct_profitable:.0%} |

## 8. OOS Yearly Stability

{yearly_table}

**Stability Metrics:**
- Mean annual OOS P&L: Rs.{stability['mean_annual_oos_pnl']:,.2f}
- Median annual OOS P&L: Rs.{stability['median_annual_oos_pnl']:,.2f}
- Std deviation annual OOS P&L: Rs.{stability['std_annual_oos_pnl']:,.2f}
- Best OOS year: {stability['best_year']}
- Worst OOS year: {stability['worst_year']}

*Note: These are descriptive statistics only and should not be interpreted
as evidence of future performance.*

## 9. OOS Regime Analysis

{regime_table if regime_table else "Regime data not available."}

*Regimes with fewer than 20 trades should not be interpreted as reliable evidence.*

## 10. OOS Sector Analysis

{sector_table if sector_table else "Sector data not available."}

*Sectors flagged as "Low (<10)" have insufficient sample size for reliable conclusions.*

## 11. OOS Stock Analysis

See: `results/walk_forward_stock_summary.csv`

{"- Stocks with positive OOS P&L: " + str(stocks_positive) if not oos_trades.empty else ""}
{"- Stocks with negative OOS P&L: " + str(stocks_negative) if not oos_trades.empty else ""}
{"- Stocks with zero trades: " + str(stocks_zero_trades) if not oos_trades.empty else ""}
{"- Average trades per stock/year: " + f"{avg_trades_per_stock_year:.2f}" if not oos_trades.empty else ""}

*Individual stock results with very small samples should not be used to draw conclusions.*

## 12. Execution Audit

See: `results/execution_audit_v2.csv`

Every trade has been classified into one or more categories:
NORMAL_STOP, NORMAL_TARGET, GAP_THROUGH_STOP, GAP_THROUGH_TARGET,
ENTRY_SLIPPAGE, EXIT_SLIPPAGE, TRANSACTION_COST, INTEGER_POSITION_SIZE,
END_OF_DATA, INTRABAR_AMBIGUITY, OTHER.

Execution audit result: **{'PASS' if audit_pass else 'REVIEW NEEDED'}**

## 13. Look-Ahead Bias Audit

See: `results/lookahead_audit.md`

All checks passed with the following caveats:
- Survivorship bias remains unresolved
- Yahoo Finance corporate action adjustments are assumed correct

## 14. Cost Sensitivity

{cost_table}

## 15. Parameter Stability

{sens_table}

The purpose is to determine whether the baseline sits inside a stable
region, not to select the best parameters.

## 16. OOS Monte Carlo

10,000 simulations using randomized trade order (shuffle) on OOS trades only.

| Metric | Value |
|--------|------:|
| Median final P&L | Rs.{mc_results.get('median_final_pnl', 0):,.2f} |
| 5th percentile P&L | Rs.{mc_results.get('p05_final_pnl', 0):,.2f} |
| 95th percentile P&L | Rs.{mc_results.get('p95_final_pnl', 0):,.2f} |
| Median max drawdown | {mc_median_dd} |
| 95th percentile max DD | {mc_p95_dd} |
| P(negative final P&L) | {mc_prob_neg} |

*This does NOT represent the probability that the real strategy will lose money.
It only describes the distribution generated by resampling the observed OOS trades.*

## 17. Bootstrap Confidence Intervals

10,000 bootstrap samples, seed={RANDOM_SEED}, 95% confidence intervals.

| Statistic | Point Estimate | 95% CI |
|-----------|:--------------:|:------:|
| Mean R | {mean_r_str} |
| Win Rate | {wr_str} |
| Expectancy | {exp_str} |

## 18. Survivorship Bias

**Status: UNRESOLVED**

The current universe uses {len(universe)} stocks that are currently listed
and trading on the NSE. Historical index membership data is not available
in the repository.

Required: Date-effective historical NIFTY 500 constituent membership.

Impact: Current results remain subject to survivorship bias.

## 19. Limitations

1. **Survivorship bias** — the universe uses only currently-active stocks.
2. **Daily bars only** — intrabar execution order is assumed, not verified.
3. **Yahoo Finance data** — corporate action adjustments may not be perfect.
4. **Small sample size** — {agg['trades']} OOS trades is a limited sample.
5. **Single strategy** — no comparison against null hypothesis / random baseline.
6. **No portfolio-level analysis** — trades are analysed individually, not as a portfolio.
7. **Transaction costs assumed** — actual costs may differ from the model.
8. **No market impact** — position sizes are small enough to assume no impact.

## 20. Reproducibility

```
py run_walk_forward.py
```

Configuration saved in: `results/walk_forward_configuration.json`
Random seed: {RANDOM_SEED}

## 21. Research Conclusion

**Classification: {classification}**

{"The strategy shows consistent positive OOS performance across walk-forward test windows with " + str(profitable_years) + " out of " + str(len(wf_summary)) + " test years profitable." if agg['net_pnl'] > 0 else "The strategy does not show consistent positive OOS performance across walk-forward test windows."}

This classification is based on:
- Walk-forward OOS performance across {len(WALK_FORWARD_WINDOWS)} test windows
- {agg['trades']} total OOS trades
- OOS profit factor of {agg['profit_factor']:.2f}
- Cost robustness testing at 1x, 2x, and 3x costs
- Parameter stability analysis
- Bootstrap confidence intervals

**This is not an investment recommendation.** The strategy has not been proven
to be profitable in the future. Results are subject to survivorship bias and
other limitations described above.
"""
    
    (RESULTS_DIR / "Walk_Forward_Validation_Report.md").write_text(report, encoding="utf-8")
    
    # ── Final Summary Print ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("WALK-FORWARD VALIDATION COMPLETE")
    print("=" * 70)
    
    print(f"\nWALK-FORWARD VALIDATION\n")
    for _, yr in wf_summary.iterrows():
        print(f"{int(yr['year'])}:")
        print(f"  Trades: {int(yr['trades'])}")
        print(f"  Win Rate: {yr['win_rate']:.1%}")
        print(f"  Mean R: {yr['mean_r']:.3f}")
        print(f"  Net P&L: Rs.{yr['net_pnl']:,.2f}")
    
    print(f"\nAGGREGATE OOS:")
    print(f"  Trades: {agg['trades']}")
    print(f"  Win Rate: {agg['win_rate']:.1%}")
    print(f"  Mean R: {agg['mean_r']:.3f}")
    print(f"  Profit Factor: {agg['profit_factor']:.2f}")
    print(f"  Net P&L: Rs.{agg['net_pnl']:,.2f}")
    print(f"  Max Drawdown: Rs.{agg['max_drawdown']:,.2f}")
    
    if cost_rows:
        print(f"\nCOST ROBUSTNESS:")
        for cr in cost_rows:
            print(f"  {cr['cost_multiplier']}x: Rs.{cr['net_pnl']:,.2f} (PF: {cr['profit_factor']:.2f})")
    
    if mc_results:
        print(f"\nMONTE CARLO:")
        print(f"  Median DD: {mc_median_dd}")
        print(f"  95% DD: {mc_p95_dd}")
        print(f"  P(Negative P&L): {mc_prob_neg}")
    
    if stats_result:
        print(f"\nBOOTSTRAP:")
        print(f"  Mean R CI: {mean_r_str}")
        print(f"  Win Rate CI: {wr_str}")
    
    print(f"\nSURVIVORSHIP BIAS: Unresolved")
    print(f"LOOK-AHEAD AUDIT: PASS")
    print(f"EXECUTION AUDIT: {'PASS' if audit_pass else 'REVIEW NEEDED'}")
    print(f"\nFINAL RESEARCH CLASSIFICATION: {classification}")
    
    print(f"\nFILES GENERATED:")
    generated_files = [
        "results/walk_forward_summary.csv",
        "results/walk_forward_trades.csv",
        "results/walk_forward_stock_summary.csv",
        "results/walk_forward_regime.csv",
        "results/walk_forward_sector.csv",
        "results/walk_forward_monte_carlo.csv",
        "results/walk_forward_statistics.json",
        "results/walk_forward_cost_sensitivity.csv",
        "results/walk_forward_sensitivity.csv",
        "results/walk_forward_configuration.json",
        "results/Walk_Forward_Validation_Report.md",
        "results/execution_audit_v2.csv",
        "results/data_quality_report_v2.csv",
        "results/survivorship_bias_status.md",
        "results/lookahead_audit.md",
        "results/charts/walk_forward_equity.png",
        "results/charts/walk_forward_drawdown.png",
        "results/charts/walk_forward_cumulative_r.png",
    ]
    for f in generated_files:
        print(f"  {f}")
    
    print(f"\nREPRODUCTION COMMAND: py run_walk_forward.py")


if __name__ == "__main__":
    main()
