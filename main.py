import sys
import pprint
import pandas as pd
from data.loader import DataLoader
from data.validator import DataValidator
from indicators import ema, rsi, atr
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from metrics.performance import compute_core_metrics
from config import BacktestConfig


def run_backtest(symbol: str, start: str, end: str, config: BacktestConfig):
    """Full pipeline: load -> validate -> enrich -> signal -> simulate -> report."""

    # -- 1. Load ----------------------------------------------------------
    loader = DataLoader()
    raw = loader.load(symbol, start, end)
    print(f"[Pipeline] Raw bars: {len(raw)}  ({raw.index[0].date()} -> {raw.index[-1].date()})")

    # -- 2. Validate ------------------------------------------------------
    clean, rejections = DataValidator().validate(raw)
    if len(rejections):
        print(f"[Pipeline] WARNING: Rejected {len(rejections)} invalid bars")
    print(f"[Pipeline] Clean bars: {len(clean)}")

    # -- 3. Enrich with indicators ----------------------------------------
    clean["ema50"] = ema.wilder_style_ema(clean["close"], config.strategy.ema_period)
    clean["rsi14"] = rsi.wilder_rsi(clean["close"], config.strategy.rsi_period)
    clean["atr14"] = atr.wilder_atr(clean, config.strategy.atr_period)

    warm_up = max(config.strategy.ema_period, config.strategy.rsi_period,
                  config.strategy.atr_period, config.strategy.slope_bars)
    ready = clean.iloc[warm_up:]
    print(f"[Pipeline] Bars after warm-up ({warm_up}): {len(ready)}")

    # -- 4. Generate signals & backtest -----------------------------------
    strategy = TrendPullbackStrategy(config.strategy)
    engine = BacktestEngine(strategy=strategy, config=config)
    ledger_df, equity_curve = engine.run(ready, symbol=symbol)

    # -- 5. Compute metrics -----------------------------------------------
    metrics = compute_core_metrics(ledger_df)

    return ledger_df, metrics, equity_curve


# -- CLI ------------------------------------------------------------------
if __name__ == "__main__":
    # Defaults — a well-known liquid NSE stock over 4+ years
    symbol = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    start  = sys.argv[2] if len(sys.argv) > 2 else "2020-01-01"
    end    = sys.argv[3] if len(sys.argv) > 3 else "2025-12-31"

    config = BacktestConfig()
    ledger, metrics, equity = run_backtest(symbol, start, end, config)

    print("\n" + "=" * 60)
    print("  BACKTEST RESULTS")
    print("=" * 60)
    pprint.pprint(metrics)

    if not ledger.empty:
        print(f"\n{'-' * 60}")
        print(f"  TRADE LOG  ({len(ledger)} trades)")
        print(f"{'-' * 60}")
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)
        print(ledger.to_string(index=False))
    else:
        print("\nNo trades were generated.")
