import pandas as pd
import numpy as np
import json
import math
from pathlib import Path

RESULTS_DIR = Path("d:/stratergy/results")
SCRATCH_DIR = Path("d:/stratergy/scratch")

def audit_random_control():
    print("--- 1. AUDIT RANDOM CONTROL ---")
    rc_df = pd.read_csv(RESULTS_DIR / "random_control_results.csv")
    actual_mean_r = 0.3357
    actual_pnl = 71285.61
    actual_pf = 1.59
    
    mean_random_pnl = rc_df["net_pnl"].mean()
    median_random_pnl = rc_df["net_pnl"].median()
    std_random_pnl = rc_df["net_pnl"].std()
    mean_random_r = rc_df["mean_r"].mean()
    
    N = len(rc_df)
    # p-value for R multiple
    # H0: Strategy signal contains no useful information beyond the matched random process.
    # We check if actual_mean_r > random_mean_r. The p-value formula: (count(random >= actual) + 1) / (N + 1)
    count_geq = (rc_df["mean_r"] >= actual_mean_r).sum()
    p_value = (count_geq + 1) / (N + 1)
    percentile = (1 - p_value) * 100
    
    print(f"Mean Random P&L: {mean_random_pnl:.2f}")
    print(f"Median Random P&L: {median_random_pnl:.2f}")
    print(f"Std Random P&L: {std_random_pnl:.2f}")
    print(f"Mean Random R: {mean_random_r:.4f}")
    print(f"Count >= Actual R: {count_geq}")
    print(f"Empirical p-value: {p_value:.4f}")
    print(f"Actual percentile: {percentile:.2f}%")
    
    return {
        "mean_random_pnl": mean_random_pnl,
        "median_random_pnl": median_random_pnl,
        "std_random_pnl": std_random_pnl,
        "mean_random_r": mean_random_r,
        "p_value": p_value,
        "percentile": percentile
    }

def audit_portfolio(risk_level="05"):
    print(f"\n--- 2-9. AUDIT PORTFOLIO {risk_level} ---")
    trades = pd.read_csv(RESULTS_DIR / f"portfolio_trades_{risk_level}.csv")
    history = pd.read_csv(RESULTS_DIR / f"portfolio_history_{risk_level}.csv")
    
    history["date"] = pd.to_datetime(history["date"])
    # recreate daily series
    start_date = history["date"].min()
    end_date = history["date"].max()
    all_days = pd.date_range(start_date, end_date, freq='D')
    
    # Forward fill the equity
    history_daily = history.set_index("date").reindex(all_days).ffill().reset_index()
    history_daily.rename(columns={"index": "date"}, inplace=True)
    
    initial_capital = history_daily["capital"].iloc[0]
    final_capital = history_daily["capital"].iloc[-1]
    
    # 4. CAGR
    days = (end_date - start_date).days
    years = days / 365.25
    cagr = (final_capital / initial_capital) ** (1 / years) - 1
    
    # 5. Drawdown
    history_daily["peak"] = history_daily["capital"].cummax()
    history_daily["drawdown_abs"] = history_daily["peak"] - history_daily["capital"]
    history_daily["drawdown_pct"] = history_daily["drawdown_abs"] / history_daily["peak"]
    max_dd_pct = history_daily["drawdown_pct"].max()
    max_dd_abs = history_daily["drawdown_abs"].max()
    
    trough_idx = history_daily["drawdown_pct"].idxmax()
    trough_date = history_daily.loc[trough_idx, "date"]
    peak_date = history_daily.loc[:trough_idx, "peak"].idxmax()
    peak_date = history_daily.loc[peak_date, "date"]
    
    # 3. Sharpe
    daily_returns = history_daily["capital"].pct_change().dropna()
    sharpe = np.sqrt(252) * (daily_returns.mean() / daily_returns.std()) if daily_returns.std() != 0 else 0
    
    # 6. Profit Factor
    gross_profit = trades.loc[trades["net_pnl"] > 0, "net_pnl"].sum()
    gross_loss = abs(trades.loc[trades["net_pnl"] <= 0, "net_pnl"].sum())
    pf = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    print(f"Initial Capital: {initial_capital}")
    print(f"Final Capital: {final_capital}")
    print(f"CAGR: {cagr*100:.2f}%")
    print(f"Max DD %: {max_dd_pct*100:.2f}%")
    print(f"Max DD Abs: {max_dd_abs:.2f}")
    print(f"Peak Date: {peak_date}, Trough Date: {trough_date}")
    print(f"Sharpe: {sharpe:.2f}")
    print(f"Profit Factor: {pf:.2f}")
    
    return {
        "cagr": cagr,
        "max_dd_pct": max_dd_pct,
        "sharpe": sharpe,
        "pf": pf
    }

if __name__ == "__main__":
    audit_random_control()
    res_05 = audit_portfolio("05")
    res_10 = audit_portfolio("10")
    
    # Write corrected risk results
    corrected_risk = pd.DataFrame([
        {"risk_level": "0.5%", "cagr": res_05["cagr"], "max_dd": res_05["max_dd_pct"], "sharpe": res_05["sharpe"], "profit_factor": res_05["pf"]},
        {"risk_level": "1.0%", "cagr": res_10["cagr"], "max_dd": res_10["max_dd_pct"], "sharpe": res_10["sharpe"], "profit_factor": res_10["pf"]}
    ])
    corrected_risk.to_csv(RESULTS_DIR / "portfolio_risk_results_corrected.csv", index=False)
