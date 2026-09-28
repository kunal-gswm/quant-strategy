import pandas as pd
import numpy as np
from pathlib import Path
import os
import json
from scipy import stats

RESULTS_DIR = Path("d:/stratergy/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WALK_FORWARD_WINDOWS = [
    {"test_year": 2021, "start": "2021-01-01", "end": "2021-12-31"},
    {"test_year": 2022, "start": "2022-01-01", "end": "2022-12-31"},
    {"test_year": 2023, "start": "2023-01-01", "end": "2023-12-31"},
    {"test_year": 2024, "start": "2024-01-01", "end": "2024-12-31"},
    {"test_year": 2025, "start": "2025-01-01", "end": "2025-12-31"},
]

def analyze_boundaries(trades_df):
    boundary_trades = []
    
    entry_oos_trades = []
    exit_oos_trades = []
    
    for _, row in trades_df.iterrows():
        entry_ts = row["entry_timestamp"]
        exit_ts = row["exit_timestamp"]
        
        # Determine entry fold
        entry_fold = None
        for w in WALK_FORWARD_WINDOWS:
            if w["start"] <= entry_ts.strftime("%Y-%m-%d") <= w["end"]:
                entry_fold = w["test_year"]
                break
                
        # Determine exit fold
        exit_fold = None
        for w in WALK_FORWARD_WINDOWS:
            if w["start"] <= exit_ts.strftime("%Y-%m-%d") <= w["end"]:
                exit_fold = w["test_year"]
                break
                
        # Classify for entry-based OOS
        if entry_fold is not None:
            r = row.copy()
            r["fold"] = entry_fold
            entry_oos_trades.append(r)
            
        # Classify for exit-based OOS
        if exit_fold is not None:
            r = row.copy()
            r["fold"] = exit_fold
            exit_oos_trades.append(r)
            
        # Classify boundary conditions
        if entry_fold != exit_fold:
            # It crosses a year boundary
            if entry_fold is None and exit_fold is not None:
                # Entered before 2021, exited in OOS
                c = "TRAINING_ENTRY_OOS_EXIT"
                f = exit_fold
            elif entry_fold is not None and exit_fold is None:
                # Entered in OOS, exited after 2025? Or just wait, exit must be > entry so if exit is None it means > 2025
                c = "OOS_ENTRY_FUTURE_EXIT"
                f = entry_fold
            else:
                # Entered in one OOS year, exited in another
                c = "OOS_ENTRY_OOS_EXIT_CROSS"
                f = f"{entry_fold}_{exit_fold}"
            
            boundary_trades.append({
                "fold": f,
                "symbol": row["symbol"],
                "signal_timestamp": row["signal_timestamp"],
                "entry_timestamp": row["entry_timestamp"],
                "exit_timestamp": row["exit_timestamp"],
                "classification": c,
                "pnl": row["net_pnl"],
                "R": row["r_multiple"]
            })
        else:
            if entry_fold is not None:
                boundary_trades.append({
                    "fold": entry_fold,
                    "symbol": row["symbol"],
                    "signal_timestamp": row["signal_timestamp"],
                    "entry_timestamp": row["entry_timestamp"],
                    "exit_timestamp": row["exit_timestamp"],
                    "classification": "PURE_OOS",
                    "pnl": row["net_pnl"],
                    "R": row["r_multiple"]
                })
                
    pd.DataFrame(boundary_trades).to_csv(RESULTS_DIR / "walk_forward_boundary_trades.csv", index=False)
    
    return pd.DataFrame(entry_oos_trades), pd.DataFrame(exit_oos_trades), pd.DataFrame(boundary_trades)

def bootstrap_metric(metric_func, data, n_iterations=1000, seed=42):
    rng = np.random.default_rng(seed)
    values = []
    n = len(data)
    if n == 0: return (0, 0)
    for _ in range(n_iterations):
        sample = rng.choice(data, size=n, replace=True)
        values.append(metric_func(sample))
    return np.percentile(values, 2.5), np.percentile(values, 97.5)

def calc_metrics(df):
    if len(df) == 0:
        return {}
    wins = len(df[df["net_pnl"] > 0])
    win_rate = wins / len(df)
    mean_r = df["r_multiple"].mean()
    expectancy = mean_r # Simplified expectancy in terms of R
    gross_profit = df[df["net_pnl"] > 0]["net_pnl"].sum()
    gross_loss = abs(df[df["net_pnl"] <= 0]["net_pnl"].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else np.inf
    net_pnl = df["net_pnl"].sum()
    
    # Win rate CI (Wilson score or bootstrap, we'll use normal approximation for simplicity or bootstrap)
    # The prompt asks for "Win-rate 95% confidence interval"
    # Using normal approx for binomial:
    z = 1.96
    margin = z * np.sqrt((win_rate * (1 - win_rate)) / len(df))
    wr_ci = (max(0, win_rate - margin), min(1, win_rate + margin))
    
    r_ci = bootstrap_metric(np.mean, df["r_multiple"].values)
    exp_ci = r_ci # Expectancy in terms of mean R
    
    return {
        "trades": len(df),
        "win_rate": win_rate,
        "win_rate_ci_lower": wr_ci[0],
        "win_rate_ci_upper": wr_ci[1],
        "mean_r": mean_r,
        "mean_r_ci_lower": r_ci[0],
        "mean_r_ci_upper": r_ci[1],
        "expectancy_ci_lower": exp_ci[0],
        "expectancy_ci_upper": exp_ci[1],
        "profit_factor": pf,
        "net_pnl": net_pnl,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss
    }

def main():
    baseline_trades = pd.read_csv("d:/stratergy/expanded_trades.csv")
    baseline_trades["entry_timestamp"] = pd.to_datetime(baseline_trades["entry_timestamp"])
    baseline_trades["exit_timestamp"] = pd.to_datetime(baseline_trades["exit_timestamp"])
    if "r_multiple" not in baseline_trades.columns:
        baseline_trades["r_multiple"] = baseline_trades["net_pnl"] / (baseline_trades["quantity"] * (baseline_trades["entry_price"] - baseline_trades["stop_price"]))
        
    entry_oos, exit_oos, boundary = analyze_boundaries(baseline_trades)
    
    m_entry = calc_metrics(entry_oos)
    m_exit = calc_metrics(exit_oos)
    
    pd.DataFrame([m_entry]).to_csv(RESULTS_DIR / "oos_entry_based_metrics.csv", index=False)
    from fix_walk_forward import load_data
    from run_final_validation import compute_all_possible_trades
    from config import BacktestConfig
    
    cfg = BacktestConfig()
    prepared_data = load_data(baseline_trades["symbol"].unique())
    from indicators import ema, rsi, atr
    for sym, df in prepared_data.items():
        if df is not None and not df.empty:
            df["ema50"] = ema.wilder_style_ema(df["Close"] if "Close" in df.columns else df["close"], cfg.strategy.ema_period)
            df["rsi14"] = rsi.wilder_rsi(df["Close"] if "Close" in df.columns else df["close"], cfg.strategy.rsi_period)
            df["atr14"] = atr.wilder_atr(df, cfg.strategy.atr_period)
            
    all_possible = compute_all_possible_trades(prepared_data, cfg)
    
    def fast_random_control(baseline_df, all_poss_df, n_simulations=10000):
        print("Running fast random control...")
        baseline_df = baseline_df.copy()
        baseline_df["year"] = pd.to_datetime(baseline_df["signal_timestamp"]).dt.year
        trade_counts = baseline_df.groupby(["symbol", "year"]).size().reset_index(name="count")
        grouped = all_poss_df.groupby(["symbol", "year"])
        poss_dict = {k: v.index.values for k, v in grouped}
        
        # Precompute lists
        counts = []
        avails = []
        for _, row in trade_counts.iterrows():
            k = (row["symbol"], row["year"])
            if k in poss_dict:
                av = poss_dict[k]
                if len(av) > 0:
                    counts.append(min(row["count"], len(av)))
                    avails.append(av)
                    
        r_mults = all_poss_df["r_multiple"].values
        mean_rs = []
        rng = np.random.default_rng(42)
        for _ in range(n_simulations):
            s_idx = []
            for c, av in zip(counts, avails):
                s_idx.extend(rng.choice(av, size=c, replace=False))
            mean_rs.append(np.mean(r_mults[s_idx]) if len(s_idx) > 0 else 0)
        return pd.DataFrame({"mean_r": mean_rs})
        
    print("Running random control for entry-based...")
    rc_entry = fast_random_control(entry_oos, all_possible, n_simulations=10000)
    actual_entry_r = m_entry["mean_r"]
    entry_p = (rc_entry["mean_r"] >= actual_entry_r).mean()
    
    print("Running random control for exit-based...")
    rc_exit = fast_random_control(exit_oos, all_possible, n_simulations=10000)
    actual_exit_r = m_exit["mean_r"]
    exit_p = (rc_exit["mean_r"] >= actual_exit_r).mean()
    
    rc_metrics = {
        "entry_actual_mean_r": actual_entry_r,
        "entry_random_mean_r": rc_entry["mean_r"].mean(),
        "entry_p_value": entry_p,
        "exit_actual_mean_r": actual_exit_r,
        "exit_random_mean_r": rc_exit["mean_r"].mean(),
        "exit_p_value": exit_p
    }
    pd.DataFrame([rc_metrics]).to_csv(RESULTS_DIR / "oos_randomization_comparison.csv", index=False)
    
    # Portfolio Boundary Handling
    from portfolio_engine import simulate_portfolio, calculate_portfolio_metrics
    
    # Portfolio Boundary Handling
    from portfolio_engine import simulate_portfolio
    all_oos_df = pd.concat([exit_oos], ignore_index=True)
    fcap, exec_trds, hist = simulate_portfolio(all_oos_df, prepared_data, cfg, risk_pct=0.005)
    
    boundary_accounting = []
    for window in WALK_FORWARD_WINDOWS:
        fold = window["test_year"]
        t_start = pd.to_datetime(window["start"])
        t_end = pd.to_datetime(window["end"])
        
        # Get history for the fold
        fold_hist = hist[(hist["date"] >= t_start) & (hist["date"] <= t_end)]
        if len(fold_hist) == 0:
            continue
            
        start_state = fold_hist.iloc[0]
        end_state = fold_hist.iloc[-1]
        
        # Pre-existing positions: trades in exec_trds that entered before t_start but exit after
        pre_existing = exec_trds[(exec_trds["entry_timestamp"] < t_start) & (exec_trds["exit_timestamp"] >= t_start)]
        cap_committed = (pre_existing["qty"] * pre_existing["entry_price"]).sum()
        
        # OOS entries
        oos_entries = len(exec_trds[(exec_trds["entry_timestamp"] >= t_start) & (exec_trds["entry_timestamp"] <= t_end)])
        
        # OOS exits
        oos_exits = len(exec_trds[(exec_trds["exit_timestamp"] >= t_start) & (exec_trds["exit_timestamp"] <= t_end)])
        
        # Realized OOS P&L
        realized_pnl = exec_trds[(exec_trds["exit_timestamp"] >= t_start) & (exec_trds["exit_timestamp"] <= t_end)]["net_pnl"].sum()
        
        boundary_accounting.append({
            "fold": fold,
            "starting_equity": start_state["equity"],
            "capital_committed_to_pre_existing": cap_committed,
            "oos_entries": oos_entries,
            "oos_exits": oos_exits,
            "realized_oos_pnl": realized_pnl,
            "unrealized_pnl_at_test_start": start_state["unrealized_pnl"],
            "ending_equity": end_state["equity"]
        })
        
    pd.DataFrame(boundary_accounting).to_csv(RESULTS_DIR / "oos_boundary_accounting.csv", index=False)


if __name__ == "__main__":
    main()
