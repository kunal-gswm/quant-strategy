import pandas as pd
import numpy as np
import json
import math
from pathlib import Path

RESULTS_DIR = Path("d:/stratergy/results")
SCRATCH_DIR = Path("d:/stratergy/scratch")

def audit_portfolio_corrected(risk_level="05"):
    print(f"\n--- RE-CALCULATING PORTFOLIO {risk_level} WITH TRUE EQUITY ---")
    trades = pd.read_csv(RESULTS_DIR / f"portfolio_trades_{risk_level}.csv")
    trades["entry_timestamp"] = pd.to_datetime(trades["entry_timestamp"])
    trades["exit_timestamp"] = pd.to_datetime(trades["exit_timestamp"])
    
    start_date = trades["entry_timestamp"].min()
    end_date = trades["exit_timestamp"].max()
    all_days = pd.date_range(start_date, end_date, freq='D')
    
    equity_curve = []
    initial_capital = 1_000_000
    
    for current_date in all_days:
        realized_pnl = trades[trades["exit_timestamp"] <= current_date]["net_pnl"].sum()
        
        active_trades = trades[(trades["entry_timestamp"] <= current_date) & (trades["exit_timestamp"] > current_date)]
        unrealized_pnl = 0
        open_positions = len(active_trades)
        
        for _, row in active_trades.iterrows():
            total_duration = (row["exit_timestamp"] - row["entry_timestamp"]).days
            if total_duration > 0:
                elapsed = (current_date - row["entry_timestamp"]).days
                unrealized_pnl += row["net_pnl"] * (elapsed / total_duration)
                
        equity = initial_capital + realized_pnl + unrealized_pnl
        equity_curve.append({
            "date": current_date,
            "equity": equity,
            "open_positions": open_positions
        })
        
    eq_df = pd.DataFrame(equity_curve)
    
    final_capital = eq_df["equity"].iloc[-1]
    
    days = (end_date - start_date).days
    years = days / 365.25
    cagr = (final_capital / initial_capital) ** (1 / years) - 1
    
    eq_df["peak"] = eq_df["equity"].cummax()
    eq_df["drawdown_pct"] = (eq_df["peak"] - eq_df["equity"]) / eq_df["peak"]
    max_dd_pct = eq_df["drawdown_pct"].max()
    
    daily_returns = eq_df["equity"].pct_change().dropna()
    sharpe = np.sqrt(252) * (daily_returns.mean() / daily_returns.std()) if daily_returns.std() != 0 else 0
    
    gross_profit = trades.loc[trades["net_pnl"] > 0, "net_pnl"].sum()
    gross_loss = abs(trades.loc[trades["net_pnl"] <= 0, "net_pnl"].sum())
    pf = gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    net_return = (final_capital - initial_capital) / initial_capital
    
    print(f"Final Capital: {final_capital:.2f}")
    print(f"CAGR: {cagr*100:.2f}%")
    print(f"Max DD %: {max_dd_pct*100:.2f}%")
    print(f"Sharpe: {sharpe:.2f}")
    print(f"Profit Factor: {pf:.2f}")
    
    return {
        "cagr": cagr,
        "max_dd": max_dd_pct,
        "sharpe": sharpe,
        "profit_factor": pf,
        "net_return": net_return
    }

if __name__ == "__main__":
    res_05 = audit_portfolio_corrected("05")
    res_10 = audit_portfolio_corrected("10")
    
    corrected_risk = pd.DataFrame([
        {"risk_level": "0.5%", "cagr": res_05["cagr"], "max_dd": res_05["max_dd"], "sharpe": res_05["sharpe"], "profit_factor": res_05["profit_factor"], "net_return": res_05["net_return"]},
        {"risk_level": "1.0%", "cagr": res_10["cagr"], "max_dd": res_10["max_dd"], "sharpe": res_10["sharpe"], "profit_factor": res_10["profit_factor"], "net_return": res_10["net_return"]}
    ])
    corrected_risk.to_csv(RESULTS_DIR / "portfolio_risk_results_corrected.csv", index=False)
