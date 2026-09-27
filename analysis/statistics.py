"""Statistical significance analysis (Section 16).

Provides:
  - Wilson score confidence interval for win rate
  - Bootstrap confidence intervals for expectancy, mean R
  - Probability of negative expectancy under resampling
"""

import numpy as np
import math


def wilson_ci(wins: int, total: int, z: float = 1.96) -> tuple:
    """Wilson score interval for a binomial proportion (win rate).
    Returns (lower, upper) at approximately 95% confidence (z=1.96)."""
    if total == 0:
        return (float("nan"), float("nan"))
    p_hat = wins / total
    denom = 1 + z**2 / total
    centre = (p_hat + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def bootstrap_ci(data: np.ndarray, stat_fn=np.mean,
                 n_boot: int = 10_000, ci: float = 0.95,
                 seed: int = 42) -> dict:
    """Bootstrap confidence interval for an arbitrary statistic.

    Parameters
    ----------
    data : 1-D array of observations (e.g., per-trade P&L or R-multiples)
    stat_fn : function to compute the statistic (default: np.mean)
    n_boot : number of bootstrap resamples
    ci : confidence level (e.g. 0.95)
    seed : random seed

    Returns
    -------
    dict with keys: observed, mean_boot, ci_lower, ci_upper, se_boot,
                    prob_negative (fraction of bootstrap samples < 0)
    """
    rng = np.random.default_rng(seed)
    n = len(data)

    if n == 0:
        return {
            "observed": float("nan"),
            "mean_boot": float("nan"),
            "ci_lower": float("nan"),
            "ci_upper": float("nan"),
            "se_boot": float("nan"),
            "prob_negative": float("nan"),
        }

    observed = float(stat_fn(data))
    boot_stats = np.empty(n_boot)

    for i in range(n_boot):
        sample = rng.choice(data, size=n, replace=True)
        boot_stats[i] = stat_fn(sample)

    alpha = (1 - ci) / 2
    lower = float(np.percentile(boot_stats, 100 * alpha))
    upper = float(np.percentile(boot_stats, 100 * (1 - alpha)))

    return {
        "observed": observed,
        "mean_boot": float(boot_stats.mean()),
        "ci_lower": lower,
        "ci_upper": upper,
        "se_boot": float(boot_stats.std()),
        "prob_negative": float((boot_stats < 0).mean()),
        "distribution": boot_stats,
    }


def full_statistical_analysis(trades_pnl: np.ndarray,
                              trades_r: np.ndarray,
                              wins: int, total: int) -> dict:
    """Run all statistical tests and return a summary dict."""
    wr_ci = wilson_ci(wins, total)

    pnl_boot = bootstrap_ci(trades_pnl, stat_fn=np.mean, n_boot=10_000)
    r_boot   = bootstrap_ci(trades_r, stat_fn=np.mean, n_boot=10_000)
    r_median_boot = bootstrap_ci(trades_r, stat_fn=np.median, n_boot=10_000)

    return {
        "n_trades": total,
        "n_wins": wins,
        "win_rate": wins / total if total > 0 else float("nan"),
        "win_rate_ci_95": wr_ci,
        "expectancy_pnl": pnl_boot,
        "mean_r": r_boot,
        "median_r": r_median_boot,
    }
