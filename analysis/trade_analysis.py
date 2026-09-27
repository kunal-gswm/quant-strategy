"""Trade distribution and R-multiple analysis (Sections 12, 13)."""

import numpy as np
import pandas as pd


def trade_concentration(trades: pd.DataFrame) -> dict:
    """Analyze whether aggregate P&L depends on a few outlier trades."""
    if trades.empty:
        return {}

    pnl = trades["net_pnl"].sort_values(ascending=False).values
    total_pnl = pnl.sum()
    winners = pnl[pnl > 0]
    losers  = pnl[pnl <= 0]

    total_profit = winners.sum() if len(winners) else 0.0
    total_loss   = losers.sum() if len(losers) else 0.0

    def top_n_contribution(n):
        top = pnl[:n].sum() if len(pnl) >= n else pnl.sum()
        return top, (top / total_pnl * 100) if total_pnl != 0 else float("nan")

    top1_abs, top1_pct = top_n_contribution(1)
    top3_abs, top3_pct = top_n_contribution(3)
    top5_abs, top5_pct = top_n_contribution(5)

    # What happens if we remove top N winners?
    if len(winners) >= 1:
        without_top1 = total_pnl - winners[0]
    else:
        without_top1 = total_pnl
    if len(winners) >= 3:
        without_top3 = total_pnl - winners[:3].sum()
    else:
        without_top3 = total_pnl - winners.sum() if len(winners) else total_pnl

    return {
        "total_pnl": float(total_pnl),
        "total_profit_from_winners": float(total_profit),
        "total_loss_from_losers": float(total_loss),
        "top1_trade_pnl": float(top1_abs),
        "top1_trade_pct": float(top1_pct),
        "top3_trade_pnl": float(top3_abs),
        "top3_trade_pct": float(top3_pct),
        "top5_trade_pnl": float(top5_abs),
        "top5_trade_pct": float(top5_pct),
        "pnl_without_top1_winner": float(without_top1),
        "pnl_without_top3_winners": float(without_top3),
        "still_positive_without_top1": without_top1 > 0,
        "still_positive_without_top3": without_top3 > 0,
        "mean_winner": float(winners.mean()) if len(winners) else 0.0,
        "median_winner": float(np.median(winners)) if len(winners) else 0.0,
        "mean_loser": float(losers.mean()) if len(losers) else 0.0,
        "median_loser": float(np.median(losers)) if len(losers) else 0.0,
    }


def r_multiple_analysis(trades: pd.DataFrame) -> dict:
    """Detailed R-multiple distribution analysis."""
    if trades.empty or "r_multiple" not in trades.columns:
        return {}

    r = trades["r_multiple"].dropna().values
    if len(r) == 0:
        return {}

    winners_r = r[r > 0]
    losers_r  = r[r <= 0]

    return {
        "mean_r": float(r.mean()),
        "median_r": float(np.median(r)),
        "std_r": float(r.std()),
        "min_r": float(r.min()),
        "max_r": float(r.max()),
        "n_total": len(r),
        "n_winners": len(winners_r),
        "n_losers": len(losers_r),
        "mean_win_r": float(winners_r.mean()) if len(winners_r) else 0.0,
        "median_win_r": float(np.median(winners_r)) if len(winners_r) else 0.0,
        "std_win_r": float(winners_r.std()) if len(winners_r) > 1 else 0.0,
        "mean_loss_r": float(losers_r.mean()) if len(losers_r) else 0.0,
        "median_loss_r": float(np.median(losers_r)) if len(losers_r) else 0.0,
        "std_loss_r": float(losers_r.std()) if len(losers_r) > 1 else 0.0,
        "all_r": r,
        "win_r": winners_r,
        "loss_r": losers_r,
    }


def trade_frequency(trades: pd.DataFrame, n_stocks: int,
                    eval_years: int = 6) -> dict:
    """Trade frequency analysis (Section 8)."""
    if trades.empty:
        return {
            "total_trades": 0,
            "trades_per_stock": 0,
            "trades_per_stock_per_year": 0,
            "trades_per_100_stocks_per_year": 0,
        }

    total = len(trades)
    per_stock = total / n_stocks if n_stocks else 0
    per_stock_per_year = per_stock / eval_years if eval_years else 0

    # By year
    trades_cp = trades.copy()
    trades_cp["year"] = pd.to_datetime(trades_cp["signal_timestamp"]).dt.year
    by_year = trades_cp.groupby("year").size().to_dict()

    # By cap
    by_cap = {}
    if "cap" in trades_cp.columns:
        by_cap = trades_cp.groupby("cap").size().to_dict()

    # By sector
    by_sector = {}
    if "sector" in trades_cp.columns:
        by_sector = trades_cp.groupby("sector").size().to_dict()

    # Per-symbol counts
    per_symbol = trades_cp.groupby("symbol").size()

    return {
        "total_trades": total,
        "n_stocks_in_universe": n_stocks,
        "trades_per_stock": per_stock,
        "trades_per_stock_per_year": per_stock_per_year,
        "trades_per_100_stocks_per_year": per_stock_per_year * 100,
        "by_year": by_year,
        "by_cap": by_cap,
        "by_sector": by_sector,
        "stocks_with_trades": int((per_symbol > 0).sum()),
        "stocks_without_trades": n_stocks - int((per_symbol > 0).sum()),
        "max_trades_single_stock": int(per_symbol.max()) if len(per_symbol) else 0,
        "per_symbol": per_symbol.to_dict(),
    }


def year_by_year_analysis(trades: pd.DataFrame) -> pd.DataFrame:
    """Section 9: break results by year."""
    if trades.empty:
        return pd.DataFrame()

    trades_cp = trades.copy()
    trades_cp["year"] = pd.to_datetime(trades_cp["signal_timestamp"]).dt.year

    results = []
    for year, grp in trades_cp.groupby("year"):
        wins = grp[grp["net_pnl"] > 0]
        losses = grp[grp["net_pnl"] <= 0]
        n = len(grp)
        w = len(wins)
        gross_profit = wins["net_pnl"].sum() if len(wins) else 0
        gross_loss = abs(losses["net_pnl"].sum()) if len(losses) else 0

        r_vals = grp["r_multiple"].dropna()

        results.append({
            "Year": year,
            "Trades": n,
            "Wins": w,
            "Losses": n - w,
            "Win Rate": w / n if n else 0,
            "Net PnL": grp["net_pnl"].sum(),
            "Profit Factor": gross_profit / gross_loss if gross_loss > 0 else float("inf"),
            "Expectancy": grp["net_pnl"].mean(),
            "Avg R": float(r_vals.mean()) if len(r_vals) else 0,
            "Median R": float(r_vals.median()) if len(r_vals) else 0,
        })

    return pd.DataFrame(results)


def consecutive_analysis(pnl_series: np.ndarray) -> dict:
    """Max consecutive wins and losses."""
    max_wins = max_losses = 0
    cur_wins = cur_losses = 0

    for p in pnl_series:
        if p > 0:
            cur_wins += 1
            cur_losses = 0
            max_wins = max(max_wins, cur_wins)
        else:
            cur_losses += 1
            cur_wins = 0
            max_losses = max(max_losses, cur_losses)

    return {"max_consecutive_wins": max_wins, "max_consecutive_losses": max_losses}


def holding_period_analysis(trades: pd.DataFrame) -> dict:
    """Average and median holding period in trading days."""
    if trades.empty:
        return {"avg_holding_days": 0, "median_holding_days": 0}

    entry = pd.to_datetime(trades["entry_timestamp"])
    exit_ = pd.to_datetime(trades["exit_timestamp"])
    days = (exit_ - entry).dt.days

    return {
        "avg_holding_days": float(days.mean()),
        "median_holding_days": float(days.median()),
        "min_holding_days": int(days.min()),
        "max_holding_days": int(days.max()),
    }
