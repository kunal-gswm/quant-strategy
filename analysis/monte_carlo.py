"""Monte Carlo simulation on trade-level results (Section 17).

Methods:
  1. Shuffle: randomize trade ordering, compute equity paths
  2. Bootstrap: resample trades WITH replacement, compute equity paths

Outputs:
  - Median / 5th / 95th percentile ending equity
  - Maximum drawdown distribution
  - Longest losing streak distribution
"""

import numpy as np
import pandas as pd


def _equity_path(pnl_sequence: np.ndarray, starting_capital: float) -> np.ndarray:
    """Cumulative equity curve from a P&L sequence."""
    return starting_capital + np.cumsum(pnl_sequence)


def _max_drawdown(equity: np.ndarray) -> float:
    """Maximum drawdown in absolute terms."""
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    return dd.max()


def _max_consecutive_losses(pnl: np.ndarray) -> int:
    """Longest streak of consecutive losing trades."""
    max_streak = 0
    current = 0
    for p in pnl:
        if p < 0:
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


def run_monte_carlo(trades_pnl: np.ndarray,
                    starting_capital: float = 500_000.0,
                    n_simulations: int = 10_000,
                    method: str = "bootstrap",
                    seed: int = 42) -> dict:
    """Run Monte Carlo simulation.

    Parameters
    ----------
    trades_pnl : array of per-trade net P&L values
    starting_capital : initial equity
    n_simulations : number of trials
    method : "shuffle" (permutation) or "bootstrap" (resample w/ replacement)
    seed : random seed for reproducibility

    Returns
    -------
    dict with keys:
        ending_equity    : array of final equity values (n_simulations,)
        max_drawdowns    : array of max drawdown per trial
        max_losing_streaks : array of max consecutive losses per trial
        percentiles      : dict with 5/25/50/75/95 for ending equity & DD
    """
    rng = np.random.default_rng(seed)
    n_trades = len(trades_pnl)

    if n_trades == 0:
        return {
            "ending_equity": np.array([starting_capital]),
            "max_drawdowns": np.array([0.0]),
            "max_losing_streaks": np.array([0]),
            "percentiles": {},
            "n_simulations": 0,
            "n_trades": 0,
            "method": method,
        }

    ending_equity = np.empty(n_simulations)
    max_drawdowns = np.empty(n_simulations)
    max_losing_streaks = np.empty(n_simulations, dtype=int)

    for i in range(n_simulations):
        if method == "shuffle":
            pnl = rng.permutation(trades_pnl)
        else:  # bootstrap
            idx = rng.integers(0, n_trades, size=n_trades)
            pnl = trades_pnl[idx]

        eq = _equity_path(pnl, starting_capital)
        ending_equity[i] = eq[-1]
        max_drawdowns[i] = _max_drawdown(eq)
        max_losing_streaks[i] = _max_consecutive_losses(pnl)

    pcts = [5, 25, 50, 75, 95]
    return {
        "ending_equity": ending_equity,
        "max_drawdowns": max_drawdowns,
        "max_losing_streaks": max_losing_streaks,
        "percentiles": {
            "ending_equity": {p: np.percentile(ending_equity, p) for p in pcts},
            "max_drawdown": {p: np.percentile(max_drawdowns, p) for p in pcts},
            "max_losing_streak": {p: int(np.percentile(max_losing_streaks, p)) for p in pcts},
        },
        "prob_negative_pnl": float((ending_equity < starting_capital).mean()),
        "n_simulations": n_simulations,
        "n_trades": n_trades,
        "method": method,
    }
