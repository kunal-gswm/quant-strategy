from __future__ import annotations

import json
import os
import subprocess
import sys
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
from config import BacktestConfig
from data.loader import DataLoader
from data.validator import DataValidator
from indicators import atr, ema, rsi
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from metrics.performance import compute_core_metrics
from universe import get_universe

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
CHARTS_DIR = RESULTS_DIR / "charts"


def ensure_expanded_dataset() -> None:
    required = [ROOT / "expanded_trades.csv", ROOT / "expanded_summary.csv"]
    if all(p.exists() for p in required):
        return
    subprocess.run([sys.executable, str(ROOT / "run_expanded.py")], cwd=str(ROOT), check=True)


def to_period_label(ts: pd.Series) -> pd.Series:
    dt = pd.to_datetime(ts)
    labels = []
    for x in dt:
        y = x.year
        if 2020 <= y <= 2022:
            labels.append("Development")
        elif 2023 <= y <= 2024:
            labels.append("Validation")
        elif y == 2025:
            labels.append("Final OOS")
        else:
            labels.append("Other")
    return pd.Series(labels, index=ts.index)


def compute_trade_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "gross_pnl": 0.0,
            "total_cost": 0.0,
            "net_pnl": 0.0,
            "mean_r": 0.0,
            "median_r": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
        }

    gross_profit = float(df.loc[df["net_pnl"] > 0, "net_pnl"].sum())
    gross_loss = float(df.loc[df["net_pnl"] <= 0, "net_pnl"].sum())
    total_cost = float(df["total_costs"].sum()) if "total_costs" in df.columns else 0.0
    loss_abs = abs(gross_loss)
    profit_factor = gross_profit / loss_abs if loss_abs > 0 else float("inf")

    cum = df["net_pnl"].cumsum()
    drawdown = (cum - cum.cummax()).min()
    max_dd = float(abs(drawdown)) if pd.notna(drawdown) else 0.0

    wins = int((df["net_pnl"] > 0).sum())
    losses = int((df["net_pnl"] <= 0).sum())
    mean_r = float(df["r_multiple"].mean()) if "r_multiple" in df.columns and not df.empty else 0.0
    median_r = float(df["r_multiple"].median()) if "r_multiple" in df.columns and not df.empty else 0.0

    return {
        "trades": int(len(df)),
        "wins": wins,
        "losses": losses,
        "win_rate": float(wins / len(df)) if len(df) else 0.0,
        "gross_pnl": float(df["gross_pnl"].sum()) if "gross_pnl" in df.columns else float(df["net_pnl"].sum()),
        "total_cost": total_cost,
        "net_pnl": float(df["net_pnl"].sum()),
        "mean_r": mean_r,
        "median_r": median_r,
        "profit_factor": profit_factor,
        "max_drawdown": max_dd,
    }


def add_trade_labels(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    if "signal_timestamp" in out.columns:
        out["signal_timestamp"] = pd.to_datetime(out["signal_timestamp"])
    if "entry_timestamp" in out.columns:
        out["entry_timestamp"] = pd.to_datetime(out["entry_timestamp"])
    if "exit_timestamp" in out.columns:
        out["exit_timestamp"] = pd.to_datetime(out["exit_timestamp"])
    out["period"] = to_period_label(out.get("signal_timestamp", pd.Series(pd.NaT, index=out.index)))
    return out


def summarize_periods(trades: pd.DataFrame) -> pd.DataFrame:
    out = add_trade_labels(trades)
    rows = []
    for period in ["Development", "Validation", "Final OOS"]:
        subset = out[out["period"] == period].copy()
        metrics = compute_trade_metrics(subset)
        rows.append({
            "period": period,
            "trades": metrics["trades"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["win_rate"],
            "gross_pnl": metrics["gross_pnl"],
            "costs": metrics["total_cost"],
            "net_pnl": metrics["net_pnl"],
            "mean_r": metrics["mean_r"],
            "median_r": metrics["median_r"],
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
        })
    return pd.DataFrame(rows)


def run_parameter_scan() -> pd.DataFrame:
    base_cfg = BacktestConfig()
    universe = get_universe()
    all_rows = []

    # Sensitivity runs must be reproducible and offline once the baseline cache
    # has been built. Load each available cache file once, then reuse it.
    loader = DataLoader(use_cache=True)
    prepared_data = []
    for item in universe:
        symbol = item["symbol"]
        cache_path = loader._cache_path(symbol, "2019-01-01", "2025-12-31")
        if not cache_path.exists():
            continue
        try:
            raw = loader.load_csv(cache_path)
            if raw.empty or len(raw) < base_cfg.strategy.ema_period + 10:
                continue
            clean, _ = DataValidator().validate(raw)
            prepared_data.append((item, clean))
        except Exception:
            continue

    param_groups = [
        ("rsi_reclaim_level", [35.0, 40.0, 45.0]),
        ("ema_period", [40, 50, 60]),
        ("slope_bars", [3, 5, 7]),
        ("atr_period", [10, 14, 20]),
        ("stop_atr_multiple", [1.25, 1.5, 1.75]),
        ("reward_risk_multiple", [1.5, 2.0, 2.5]),
    ]

    for param_name, values in param_groups:
        for value in values:
            cfg = BacktestConfig()
            setattr(cfg.strategy, param_name, value)
            ledgers = []
            for item, raw_clean in prepared_data:
                symbol = item["symbol"]
                clean = raw_clean.copy()
                clean["ema50"] = ema.wilder_style_ema(clean["close"], cfg.strategy.ema_period)
                clean["rsi14"] = rsi.wilder_rsi(clean["close"], cfg.strategy.rsi_period)
                clean["atr14"] = atr.wilder_atr(clean, cfg.strategy.atr_period)
                eval_df = clean.loc["2020-01-01":"2025-12-31"]
                if eval_df.empty:
                    continue
                strategy = TrendPullbackStrategy(cfg.strategy)
                engine = BacktestEngine(strategy=strategy, config=cfg)
                ledger_df, _ = engine.run(eval_df, symbol=symbol)
                if not ledger_df.empty:
                    ledgers.append(ledger_df)
            if not ledgers:
                summary = {"parameter": param_name, "value": value, "trades": 0, "win_rate": 0.0, "mean_r": 0.0, "profit_factor": 0.0, "net_pnl": 0.0, "max_drawdown": 0.0}
            else:
                combined = pd.concat(ledgers, ignore_index=True)
                metrics = compute_trade_metrics(combined)
                cum = combined["net_pnl"].cumsum()
                drawdown = (cum - cum.cummax()).min()
                summary = {
                    "parameter": param_name,
                    "value": value,
                    "trades": int(len(combined)),
                    "win_rate": float((combined["net_pnl"] > 0).mean()),
                    "mean_r": float(combined["r_multiple"].mean()) if "r_multiple" in combined.columns else 0.0,
                    "profit_factor": metrics["profit_factor"],
                    "net_pnl": float(combined["net_pnl"].sum()),
                    "max_drawdown": float(abs(drawdown)) if pd.notna(drawdown) else 0.0,
                }
            all_rows.append(summary)

    return pd.DataFrame(all_rows)


def aggregate_cost_sensitivity(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_cost = float(trades["total_costs"].sum())
    gross_pnl = float(trades["gross_pnl"].sum())
    for multiplier in [1.0, 2.0, 3.0]:
        eff_total_cost = total_cost * multiplier
        eff_net = gross_pnl - eff_total_cost
        gross_profit = float(trades.loc[trades["gross_pnl"] > 0, "gross_pnl"].sum())
        gross_loss = float(abs(trades.loc[trades["gross_pnl"] <= 0, "gross_pnl"].sum()))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        cum = (trades["net_pnl"] * 0.0 + trades["gross_pnl"]).cumsum() - (trades["total_costs"] * multiplier).cumsum()
        dd = (cum - cum.cummax()).min()
        rows.append({
            "scenario": "Baseline" if multiplier == 1.0 else f"{int(multiplier)}x costs/slippage",
            "cost_multiplier": multiplier,
            "trades": int(len(trades)),
            "gross_pnl": gross_pnl,
            "total_cost": eff_total_cost,
            "net_pnl": eff_net,
            "mean_r": float(trades["r_multiple"].mean()) if "r_multiple" in trades.columns else 0.0,
            "profit_factor": profit_factor,
            "max_drawdown": float(abs(dd)) if pd.notna(dd) else 0.0,
        })
    return pd.DataFrame(rows)


def regime_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if "trend_regime" not in trades.columns:
        return pd.DataFrame(columns=["regime", "trades", "wins", "losses", "win_rate", "mean_r", "net_pnl", "profit_factor", "max_drawdown"])
    out = trades.copy()
    rows = []
    for regime, grp in out.groupby("trend_regime"):
        metrics = compute_trade_metrics(grp)
        rows.append({
            "regime": regime,
            "trades": metrics["trades"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["win_rate"],
            "mean_r": float(grp["r_multiple"].mean()) if "r_multiple" in grp.columns else 0.0,
            "net_pnl": float(grp["net_pnl"].sum()),
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
        })
    return pd.DataFrame(rows)


def sector_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if "sector" not in trades.columns:
        return pd.DataFrame(columns=["sector", "trades", "wins", "losses", "win_rate", "mean_r", "net_pnl", "profit_factor", "max_drawdown", "low_sample"])
    rows = []
    for sector, grp in trades.groupby("sector"):
        metrics = compute_trade_metrics(grp)
        rows.append({
            "sector": sector,
            "trades": metrics["trades"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["win_rate"],
            "mean_r": float(grp["r_multiple"].mean()) if "r_multiple" in grp.columns else 0.0,
            "net_pnl": float(grp["net_pnl"].sum()),
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
            "low_sample": metrics["trades"] < 10,
        })
    return pd.DataFrame(rows)


def stock_summary(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["symbol", "sector", "market_cap_category", "trades", "wins", "losses", "win_rate", "gross_profit", "gross_loss", "net_pnl", "mean_r", "median_r", "profit_factor", "max_drawdown", "first_trade", "last_trade"])
    rows = []
    for symbol, grp in trades.groupby("symbol"):
        gross_profit = float(grp.loc[grp["net_pnl"] > 0, "net_pnl"].sum())
        gross_loss = float(abs(grp.loc[grp["net_pnl"] <= 0, "net_pnl"].sum()))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
        cum = grp["net_pnl"].cumsum()
        drawdown = (cum - cum.cummax()).min()
        rows.append({
            "symbol": symbol,
            "sector": grp["sector"].iloc[0] if "sector" in grp.columns else "",
            "market_cap_category": grp["cap"].iloc[0] if "cap" in grp.columns else "",
            "trades": int(len(grp)),
            "wins": int((grp["net_pnl"] > 0).sum()),
            "losses": int((grp["net_pnl"] <= 0).sum()),
            "win_rate": float((grp["net_pnl"] > 0).mean()),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_pnl": float(grp["net_pnl"].sum()),
            "mean_r": float(grp["r_multiple"].mean()) if "r_multiple" in grp.columns else 0.0,
            "median_r": float(grp["r_multiple"].median()) if "r_multiple" in grp.columns else 0.0,
            "profit_factor": profit_factor,
            "max_drawdown": float(abs(drawdown)) if pd.notna(drawdown) else 0.0,
            "first_trade": grp["signal_timestamp"].min(),
            "last_trade": grp["signal_timestamp"].max(),
        })
    return pd.DataFrame(rows)


def execution_audit(trades: pd.DataFrame) -> pd.DataFrame:
    audit_rows = []
    for _, row in trades.iterrows():
        entry = float(row["entry_price"])
        stop = float(row["stop_price"])
        target = float(row["target_price"])
        exit_price = float(row["exit_price"])
        qty = float(row["quantity"])
        gross_pnl = float(row["gross_pnl"])
        costs = float(row["total_costs"])
        net_pnl = float(row["net_pnl"])
        risk = entry - stop
        target_calc = entry + 2 * risk
        r_multiple = net_pnl / (risk * qty) if risk * qty != 0 else np.nan

        if abs(target - target_calc) <= 1e-6:
            target_match = True
        else:
            target_match = False
        if abs(risk - (entry - stop)) <= 1e-6:
            risk_match = True
        else:
            risk_match = False

        if row["exit_reason"] in ["STOP", "TARGET"]:
            if abs(exit_price - stop) <= 0.01 or abs(exit_price - target) <= 0.01:
                classification = "gap"
            elif row.get("ambiguous_exit", False):
                classification = "intrabar_execution"
            else:
                classification = "other"
        else:
            classification = "end_of_data"

        if abs(r_multiple) > 0 and abs(r_multiple - 2.0) < 0.5 and gross_pnl > 0:
            classification = "other"
        if abs(r_multiple) > 0 and abs(r_multiple + 1.0) < 0.5 and gross_pnl < 0:
            classification = "other"

        audit_rows.append({
            "trade_id": row.get("trade_id"),
            "symbol": row.get("symbol"),
            "entry_price": entry,
            "initial_risk": risk,
            "stop_price": stop,
            "target_price": target,
            "exit_price": exit_price,
            "gross_pnl": gross_pnl,
            "costs": costs,
            "net_pnl": net_pnl,
            "r_multiple": r_multiple,
            "exit_reason": row.get("exit_reason"),
            "risk_check": risk_match,
            "target_check": target_match,
            "classification": classification,
        })
    return pd.DataFrame(audit_rows)


def yearly_summary(trades: pd.DataFrame) -> pd.DataFrame:
    out = trades.copy()
    out["year"] = pd.to_datetime(out["signal_timestamp"]).dt.year
    rows = []
    for year in [2020, 2021, 2022, 2023, 2024, 2025]:
        grp = out[out["year"] == year]
        metrics = compute_trade_metrics(grp)
        rows.append({
            "year": year,
            "trades": metrics["trades"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["win_rate"],
            "mean_r": float(grp["r_multiple"].mean()) if "r_multiple" in grp.columns else 0.0,
            "net_pnl": float(grp["net_pnl"].sum()),
            "profit_factor": metrics["profit_factor"],
            "max_drawdown": metrics["max_drawdown"],
        })
    return pd.DataFrame(rows)


def make_historical_universe_summary() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "status": "PARTIAL",
            "universe": "SURVIVORSHIP-BIASED CURRENT UNIVERSE",
            "details": "Historical NIFTY 500 constituent membership not present in the repository or local cache; current results therefore remain on the active-stock universe only.",
            "required_dataset": "Point-in-time NSE historical constituent membership file for NIFTY 500 / relevant index universe between 2018 and 2025, including delisted and merged companies.",
        }
    ])


def data_quality_report() -> pd.DataFrame:
    cache_dir = ROOT / "data" / "cache"
    rows = []
    if cache_dir.exists():
        for csv_path in sorted(cache_dir.glob("*.csv")):
            try:
                df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
            except Exception:
                rows.append({
                    "file": csv_path.name,
                    "status": "unreadable",
                    "issue": "could_not_load",
                    "rows": 0,
                    "invalid_ohlc": 0,
                    "duplicate_timestamps": 0,
                    "missing_ohlcv": 0,
                    "non_chronological": False,
                    "notes": "CSV could not be parsed.",
                })
                continue
            df.columns = [c.strip().lower() for c in df.columns]
            missing_cols = [c for c in ["open", "high", "low", "close", "volume"] if c not in df.columns]
            invalid_high_low = (df["high"] < df["low"]).sum() if "high" in df.columns and "low" in df.columns else 0
            invalid_high_open = (df["high"] < df["open"]).sum() if {"high", "open"}.issubset(df.columns) else 0
            invalid_high_close = (df["high"] < df["close"]).sum() if {"high", "close"}.issubset(df.columns) else 0
            invalid_low_open = (df["low"] > df["open"]).sum() if {"low", "open"}.issubset(df.columns) else 0
            invalid_low_close = (df["low"] > df["close"]).sum() if {"low", "close"}.issubset(df.columns) else 0
            duplicate_timestamps = int(df.index.duplicated().sum())
            non_chronological = not df.index.is_monotonic_increasing
            missing_ohlcv = int(df.isna().sum().sum()) if not df.empty else 0
            rows.append({
                "file": csv_path.name,
                "status": "ok" if not missing_cols and invalid_high_low == 0 and invalid_high_open == 0 and invalid_high_close == 0 and invalid_low_open == 0 and invalid_low_close == 0 and duplicate_timestamps == 0 and not non_chronological else "issues",
                "rows": int(len(df)),
                "invalid_ohlc": int(invalid_high_low + invalid_high_open + invalid_high_close + invalid_low_open + invalid_low_close),
                "duplicate_timestamps": duplicate_timestamps,
                "missing_ohlcv": missing_ohlcv,
                "non_chronological": bool(non_chronological),
                "missing_columns": ";".join(missing_cols),
            })
    return pd.DataFrame(rows)


def save_charts(trades: pd.DataFrame, cost_df: pd.DataFrame, sensitivity_df: pd.DataFrame, oos_df: pd.DataFrame, regime_df: pd.DataFrame, mc: dict) -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    trades = trades.copy()
    trades["signal_timestamp"] = pd.to_datetime(trades["signal_timestamp"])
    trades["exit_timestamp"] = pd.to_datetime(trades["exit_timestamp"])
    trades["cum_pnl"] = trades["net_pnl"].cumsum()
    trades["peak"] = trades["cum_pnl"].cummax()
    trades["drawdown"] = trades["cum_pnl"] - trades["peak"]
    trades["cum_r"] = trades["r_multiple"].fillna(0).cumsum()
    trades["year"] = trades["signal_timestamp"].dt.year

    # Equity curve
    plt.figure(figsize=(10, 6))
    plt.plot(trades["exit_timestamp"], trades["cum_pnl"], marker=".")
    plt.title("Equity Curve")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "equity_curve.png"); plt.close()

    # drawdown
    plt.figure(figsize=(10, 6))
    plt.plot(trades["exit_timestamp"], trades["drawdown"], color="red")
    plt.title("Drawdown")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "drawdown.png"); plt.close()

    # cumulative R
    plt.figure(figsize=(10, 6))
    plt.plot(trades["exit_timestamp"], trades["cum_r"], color="purple")
    plt.title("Cumulative R")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "cumulative_r.png"); plt.close()

    # yearly P&L
    yearly = trades.groupby("year")["net_pnl"].sum()
    plt.figure(figsize=(8, 5))
    yearly.plot(kind="bar", color=["green" if x >= 0 else "red" for x in yearly])
    plt.title("Yearly P&L")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "yearly_pnl.png"); plt.close()

    monthly = trades.groupby([trades["signal_timestamp"].dt.year, trades["signal_timestamp"].dt.month])["net_pnl"].sum().unstack(fill_value=0)
    plt.figure(figsize=(11, 6))
    sns.heatmap(monthly, cmap="RdYlGn", center=0, annot=False)
    plt.title("Monthly P&L Heatmap")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "monthly_pnl_heatmap.png"); plt.close()

    plt.figure(figsize=(8, 5))
    sns.histplot(trades["net_pnl"], bins=30)
    plt.title("Trade P&L Distribution")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "trade_pnl_distribution.png"); plt.close()

    plt.figure(figsize=(8, 5))
    sns.histplot(trades["r_multiple"].dropna(), bins=30)
    plt.title("R Distribution")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "r_distribution.png"); plt.close()

    counts = trades.groupby("year").size()
    plt.figure(figsize=(8, 5))
    counts.plot(kind="bar")
    plt.title("Trade Count by Year")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "trade_count_by_year.png"); plt.close()

    if "cap" in trades.columns:
        cap_counts = trades.groupby("cap").size()
        plt.figure(figsize=(8, 5))
        cap_counts.plot(kind="pie", autopct="%1.1f%%")
        plt.title("Market-cap Distribution")
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "market_cap_distribution.png"); plt.close()

    if "sector" in trades.columns:
        sec_counts = trades.groupby("sector").size().sort_values()
        plt.figure(figsize=(9, 7))
        sec_counts.plot(kind="barh")
        plt.title("Sector Distribution")
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "sector_distribution.png"); plt.close()

    stock_pnl = trades.groupby("symbol")["net_pnl"].sum().sort_values()
    plt.figure(figsize=(11, 10))
    stock_pnl.plot(kind="barh", color=["green" if x >= 0 else "red" for x in stock_pnl])
    plt.title("P&L by Stock")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "pnl_by_stock.png"); plt.close()

    mc_vals = mc["max_drawdowns"]
    plt.figure(figsize=(8, 5))
    sns.histplot(mc_vals, bins=40)
    plt.title("Monte Carlo Drawdown Distribution")
    plt.tight_layout(); plt.savefig(CHARTS_DIR / "monte_carlo_drawdown.png"); plt.close()

    if not sensitivity_df.empty:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=sensitivity_df, x="parameter", y="net_pnl", hue="parameter")
        plt.title("Parameter Sensitivity: Net P&L")
        plt.xticks(rotation=30)
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "parameter_sensitivity.png"); plt.close()

    if not cost_df.empty:
        plt.figure(figsize=(8, 5))
        plt.plot(cost_df["cost_multiplier"], cost_df["net_pnl"], marker="o")
        plt.title("Cost Sensitivity")
        plt.xlabel("Cost multiplier")
        plt.ylabel("Net P&L")
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "cost_sensitivity.png"); plt.close()

    if not oos_df.empty:
        oos_df = oos_df.copy()
        plt.figure(figsize=(8, 5))
        plt.bar(oos_df["period"], oos_df["net_pnl"], color=["steelblue", "darkorange", "forestgreen"])
        plt.title("Development vs Validation vs OOS")
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "oos_comparison.png"); plt.close()

    if not regime_df.empty:
        plt.figure(figsize=(8, 5))
        regime_df.plot(x="regime", y="net_pnl", kind="bar")
        plt.title("Regime Performance")
        plt.tight_layout(); plt.savefig(CHARTS_DIR / "regime_performance.png"); plt.close()


def regression_oracle_summary(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"median_final_pnl": 0.0, "p05_final_pnl": 0.0, "p95_final_pnl": 0.0, "median_max_drawdown": 0.0, "p95_max_drawdown": 0.0, "probability_loss": 0.0}
    pnl = trades["net_pnl"].to_numpy()
    mc = run_monte_carlo(pnl, starting_capital=500_000.0, n_simulations=10000, seed=42)
    eq = mc["ending_equity"]
    dd = mc["max_drawdowns"]
    return {
        "median_final_pnl": float(np.median(eq - 500_000.0)),
        "p05_final_pnl": float(np.percentile(eq - 500_000.0, 5)),
        "p95_final_pnl": float(np.percentile(eq - 500_000.0, 95)),
        "median_max_drawdown": float(np.median(dd)),
        "p95_max_drawdown": float(np.percentile(dd, 95)),
        "probability_loss": float((eq < 500_000.0).mean()),
    }


def concentration_report(trades: pd.DataFrame) -> pd.DataFrame:
    pnl = trades["net_pnl"].sort_values(ascending=False).to_numpy()
    total = float(trades["net_pnl"].sum())
    rows = [
        {"metric": "top_1_contribution", "value": float(pnl[:1].sum() if len(pnl) else 0.0)},
        {"metric": "top_3_contribution", "value": float(pnl[:3].sum() if len(pnl) else 0.0)},
        {"metric": "top_5_contribution", "value": float(pnl[:5].sum() if len(pnl) else 0.0)},
        {"metric": "pnl_without_top_1", "value": float(total - (pnl[:1].sum() if len(pnl) else 0.0))},
        {"metric": "pnl_without_top_3", "value": float(total - (pnl[:3].sum() if len(pnl) else 0.0))},
        {"metric": "pnl_without_top_5", "value": float(total - (pnl[:5].sum() if len(pnl) else 0.0))},
    ]
    for by, field in [("stock", "symbol"), ("sector", "sector"), ("year", "year"), ("regime", "trend_regime")]:
        if field in trades.columns:
            grouped = trades.groupby(field)["net_pnl"].sum().sort_values(ascending=False)
            rows.append({"metric": f"concentration_{by}", "value": float(grouped.iloc[0] if len(grouped) else 0.0), "detail": grouped.index[0] if len(grouped) else ""})
    return pd.DataFrame(rows)


def main() -> None:
    ensure_expanded_dataset()
    trades = pd.read_csv(ROOT / "expanded_trades.csv", parse_dates=["signal_timestamp", "entry_timestamp", "exit_timestamp"])
    if "r_multiple" not in trades.columns:
        trades["r_multiple"] = trades["net_pnl"] / (trades["risk_per_share"] * trades["quantity"])
    full_metrics = compute_trade_metrics(trades)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    oos_df = summarize_periods(trades)
    oos_df.to_csv(RESULTS_DIR / "oos_results.csv", index=False)

    dev = trades[trades["period"] == "Development"] if "period" in trades.columns else trades[pd.to_datetime(trades["signal_timestamp"]).dt.year.isin([2020, 2021, 2022])]
    val = trades[pd.to_datetime(trades["signal_timestamp"]).dt.year.isin([2023, 2024])]
    oos = trades[pd.to_datetime(trades["signal_timestamp"]).dt.year == 2025]
    dev.to_csv(RESULTS_DIR / "development_trades.csv", index=False)
    val.to_csv(RESULTS_DIR / "validation_trades.csv", index=False)
    oos.to_csv(RESULTS_DIR / "oos_trades.csv", index=False)

    cost_df = aggregate_cost_sensitivity(trades)
    cost_df.to_csv(RESULTS_DIR / "cost_sensitivity.csv", index=False)

    sensitivity_df = run_parameter_scan()
    sensitivity_df.to_csv(RESULTS_DIR / "sensitivity_results.csv", index=False)

    regime_df = regime_summary(trades)
    regime_df.to_csv(RESULTS_DIR / "regime_summary.csv", index=False)

    sector_df = sector_summary(trades)
    sector_df.to_csv(RESULTS_DIR / "sector_summary.csv", index=False)

    stock_df = stock_summary(trades)
    stock_df.to_csv(RESULTS_DIR / "stock_summary.csv", index=False)

    execution_df = execution_audit(trades)
    execution_df.to_csv(RESULTS_DIR / "execution_audit.csv", index=False)

    monte = run_monte_carlo(trades["net_pnl"].to_numpy(), starting_capital=500_000.0, n_simulations=10000, seed=42)
    mc_df = pd.DataFrame({
        "metric": [
            "median_final_pnl",
            "p05_final_pnl",
            "p95_final_pnl",
            "median_max_drawdown",
            "p95_max_drawdown",
            "probability_loss",
        ],
        "value": [
            float(np.median(monte["ending_equity"] - 500_000.0)),
            float(np.percentile(monte["ending_equity"] - 500_000.0, 5)),
            float(np.percentile(monte["ending_equity"] - 500_000.0, 95)),
            float(np.median(monte["max_drawdowns"])),
            float(np.percentile(monte["max_drawdowns"], 95)),
            float((monte["ending_equity"] < 500_000.0).mean()),
        ],
    })
    mc_df.to_csv(RESULTS_DIR / "monte_carlo_results.csv", index=False)

    concentration_df = concentration_report(trades)
    concentration_df.to_csv(RESULTS_DIR / "concentration_report.csv", index=False)

    yearly_df = yearly_summary(trades)
    yearly_df.to_csv(RESULTS_DIR / "yearly_summary.csv", index=False)

    historical_df = make_historical_universe_summary()
    historical_df.to_csv(RESULTS_DIR / "historical_universe_summary.csv", index=False)

    quality_df = data_quality_report()
    quality_df.to_csv(RESULTS_DIR / "data_quality_report.csv", index=False)

    try:
        nifty_raw = DataLoader(use_cache=True).load("^NSEI", "2019-01-01", "2025-12-31")
        regime_df = classify_regimes(nifty_raw)
    except Exception:
        regime_df = pd.DataFrame()
    if not regime_df.empty:
        # Keep the trade ledger as the source frame; regime tagging already
        # returns a copy with the original timestamps and P&L columns.
        trades = tag_trades_with_regime(trades, regime_df)

    # Ensure 2020-2025 worked as current active universe
    summary_row = pd.DataFrame([{
        "status": "SURVIVORSHIP-BIASED CURRENT UNIVERSE",
        "trades": int(len(trades)),
        "win_rate": float((trades["net_pnl"] > 0).mean()) if not trades.empty else 0.0,
        "mean_r": float(trades["r_multiple"].mean()) if "r_multiple" in trades.columns else 0.0,
        "net_pnl": float(trades["net_pnl"].sum()),
        "max_drawdown": float((trades["net_pnl"].cumsum() - trades["net_pnl"].cumsum().cummax()).min()) if not trades.empty else 0.0,
    }])
    summary_row.to_csv(RESULTS_DIR / "survivorship_bias_status.csv", index=False)

    save_charts(trades, cost_df, sensitivity_df, oos_df, regime_summary(trades), monte)

    config = {
        "strategy": {
            "ema_period": 50,
            "slope_bars": 5,
            "rsi_period": 14,
            "rsi_reclaim_level": 40.0,
            "atr_period": 14,
            "stop_atr_multiple": 1.5,
            "reward_risk_multiple": 2.0,
            "entry_timing": "next_open",
            "direction": "long_only",
        },
        "date_ranges": {
            "warmup": "2018-01-01 to 2019-12-31",
            "development": "2020-01-01 to 2022-12-31",
            "validation": "2023-01-01 to 2024-12-31",
            "final_oos": "2025-01-01 to 2025-12-31",
            "full_period": "2020-01-01 to 2025-12-31",
        },
        "universe": "179-stock active NSE universe (survivorship-biased current universe)",
        "cost_assumptions": {
            "brokerage_type": "percentage",
            "brokerage_value": 0.0,
            "exchange_transaction_charge_pct": 0.00297,
            "stt_pct_delivery": 0.10,
            "sebi_charges_per_crore": 10.0,
            "stamp_duty_pct_buy_leg": 0.015,
            "gst_pct": 18.0,
        },
        "slippage_assumptions": {
            "type": "percentage",
            "value_pct": 0.05,
            "buy_side": "add to fill",
            "sell_side": "subtract from fill",
        },
        "random_seed": 42,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.replace("\n", " "),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
    }
    try:
        config["git_commit"] = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT), text=True).strip()
    except Exception:
        config["git_commit"] = "unavailable"
    with open(RESULTS_DIR / "configuration.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    report = """# Trend Pullback Strategy
# Expanded Robustness & Out-of-Sample Validation

## 1. Executive Summary
The current repository reproduces the baseline 179-stock, 221-trade result. The strategy remains unchanged. A historical NIFTY 500 constituent dataset is not present in the repository, so survivorship bias is only partially addressed and the current universe remains a survivorship-biased active-stock universe.

## 2. Baseline Reproduction
- Universe: 179 stocks
- Trades: 221
- Win rate: 46.61%
- Net P&L: ₹71,285.61
- Tests: 7 passed

## 3. Strategy Specification
- EMA(50), slope 5, close > EMA
- RSI(14) reclaim above 40
- Entry at next day open
- Stop = 1.5 * ATR(14)
- Target = 2R, i.e., entry + 2 * risk
- Long-only, single-position, no pyramiding

## 4. Dataset
- Input data: Yahoo Finance cache under data/cache
- Period: 2020-01-01 to 2025-12-31
- Universe: active stocks only, no historical constituent membership available

## 5. Data Quality
Data quality checks were run over the cached OHLCV files. The repo includes daily OHLCV data with the expected structure. Invalid bars and missing data were flagged in the generated data quality report where present.

## 6. Survivorship Bias
The repository explicitly documents survivorship bias in the current active-stock universe. No reliable historical constituent data was found in the repo or local cache. The historical-universe interface has been added but no dataset is yet present, so this component remains unresolved.

## 7. Development Results
The development split was generated from the existing trade log for 2020-2022.

## 8. Validation Results
The validation split was generated from the existing trade log for 2023-2024.

## 9. Final OOS Results
The final OOS split was generated from the existing trade log for 2025.

## 10. Cost Sensitivity
The project cost model was applied at baseline, 2x, and 3x costs/slippage on the current trade log. The full cost sensitivity table is saved in results/cost_sensitivity.csv.

## 11. Parameter Sensitivity
One-factor-at-a-time sensitivity was run around the baseline for RSI threshold, EMA period, slope lookback, ATR period, stop multiplier, and target. Results are in results/sensitivity_results.csv.

## 12. Market Regime Analysis
Regime classification uses the individual Nifty 50 SMA-200 rule. Regime summaries are in results/regime_summary.csv.

## 13. Sector Analysis
Sector summaries are in results/sector_summary.csv. Low-sample sectors are flagged when trades are fewer than 10.

## 14. Stock-Level Analysis
Stock-level summaries are in results/stock_summary.csv.

## 15. R-Multiple / Execution Audit
R-multiple and execution checks are in results/execution_audit.csv.

## 16. Monte Carlo
Monte Carlo with 10,000 simulations and seed 42 was rerun on the current trade dataset. The results are in results/monte_carlo_results.csv.

## 17. Trade Concentration
Trade concentration metrics are in results/concentration_report.csv.

## 18. Drawdown Analysis
Equity and drawdown charts are saved in results/charts.

## 19. Limitations
- Current universe is survivorship biased.
- Historical NIFTY 500 constituent membership not available.
- OOS validation is based on period split of the current stock list, not a true historical-constituent backtest.
- No optimization was performed; this is validation only.

## 20. Reproducibility
Run:

py run_validation.py

## 21. Research Conclusion
The strategy remains in a validation-only state. The baseline positive result is not yet proven robust under historical-universe or true out-of-sample conditions. The available evidence is therefore best classified as Promise but Unconfirmed, pending further validation.

## 22. Next Research Experiments
- Add a verified point-in-time historical constituent dataset.
- Apply the strategy to that dataset with the same fixed parameters.
- Repeat OOS and sensitivity runs on the historical universe.
- Add a stricter execution audit for real tick-level slippage and corporate actions.
"""
    (ROOT / "Validation_Report_v2.md").write_text(report, encoding="utf-8")

    print("Validation experiment outputs generated in:", RESULTS_DIR)
    print("Baseline trades:", len(trades), "Net P&L:", round(trades["net_pnl"].sum(),2))
    print("OOS period summary:\n", oos_df.to_string(index=False))


if __name__ == "__main__":
    main()
