import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from data.loader import DataLoader
from data.validator import DataValidator
from indicators import ema, rsi, atr
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from metrics.performance import compute_core_metrics
from config import BacktestConfig
from universe import get_universe
from analysis import monte_carlo, statistics, trade_analysis, regime

LOAD_START = "2019-01-01"
EVAL_START = "2020-01-01"
EVAL_END   = "2025-12-31"


def download_all_data(universe):
    """Download data for all stocks in parallel."""
    loader = DataLoader(use_cache=True)
    def _fetch(symbol):
        try:
            df = loader.load(symbol, LOAD_START, EVAL_END)
            return symbol, df, None
        except Exception as e:
            return symbol, pd.DataFrame(), str(e)

    results = {}
    errors = {}
    print(f"Downloading data for {len(universe)} stocks in parallel...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch, s["symbol"]): s for s in universe}
        for i, future in enumerate(as_completed(futures), 1):
            sym, df, err = future.result()
            if err:
                errors[sym] = err
            else:
                results[sym] = df
            if i % 25 == 0:
                print(f"  [{i}/{len(universe)}] {sym} processed")
    return results, errors


def run_expanded():
    config = BacktestConfig()
    universe = get_universe()

    # 1. Download data
    data_dict, errors = download_all_data(universe)
    print(f"\nData loaded: {len(data_dict)} successful, {len(errors)} failed.")

    # 2. Prepare Nifty 50 for Regime Classification
    nifty_loader = DataLoader(use_cache=True)
    try:
        nifty_raw = nifty_loader.load("^NSEI", LOAD_START, EVAL_END)
        regime_df = regime.classify_regimes(nifty_raw)
        print("Regime classification built using Nifty 50 (^NSEI)")
    except Exception as e:
        print("Failed to load Nifty 50, regime analysis will be skipped:", e)
        regime_df = pd.DataFrame()

    all_ledgers = []
    all_equity_curves = []
    symbol_summaries = []

    # 3. Run backtest per stock
    print("Running strategy simulation on valid stocks...")
    for item in universe:
        sym = item["symbol"]
        if sym not in data_dict or data_dict[sym].empty:
            continue

        raw = data_dict[sym]
        if len(raw) < config.strategy.ema_period + 10:
            continue

        clean, _ = DataValidator().validate(raw)
        clean["ema50"] = ema.wilder_style_ema(clean["close"], config.strategy.ema_period)
        clean["rsi14"] = rsi.wilder_rsi(clean["close"], config.strategy.rsi_period)
        clean["atr14"] = atr.wilder_atr(clean, config.strategy.atr_period)

        eval_df = clean.loc[EVAL_START:]
        if eval_df.empty:
            continue

        strategy = TrendPullbackStrategy(config.strategy)
        engine = BacktestEngine(strategy=strategy, config=config)
        ledger_df, eq_curve = engine.run(eval_df, symbol=sym)

        metrics = compute_core_metrics(ledger_df)
        
        # Add metadata
        row = {
            "Symbol": sym, "Name": item["name"], "Cap": item["cap"], "Sector": item["sector"],
            "Trades": metrics.get("total_trades", 0),
            "Wins": 0, "Losses": 0,
            "Win Rate": metrics.get("win_rate", float("nan")),
            "Net PnL": metrics.get("net_pnl", 0.0),
            "Profit Factor": metrics.get("profit_factor", float("nan")),
            "Expectancy": metrics.get("expectancy", float("nan")),
            "Avg R": float("nan")
        }

        if metrics.get("total_trades", 0) > 0:
            w = len(ledger_df[ledger_df["net_pnl"] > 0])
            row["Wins"] = w
            row["Losses"] = len(ledger_df) - w
            row["Avg R"] = ledger_df["r_multiple"].mean()
            
            # Tag regimes if we have Nifty 50 data
            if not regime_df.empty:
                ledger_df = regime.tag_trades_with_regime(ledger_df, regime_df)
                
            ledger_df["cap"] = item["cap"]
            ledger_df["sector"] = item["sector"]
            all_ledgers.append(ledger_df)
            
            eq_curve["symbol"] = sym
            all_equity_curves.append(eq_curve)

        symbol_summaries.append(row)

    print(f"Simulation completed. {len(all_ledgers)} stocks generated at least 1 trade.")

    # 4. Consolidate and Save
    summary_df = pd.DataFrame(symbol_summaries)
    summary_df.to_csv("expanded_summary.csv", index=False)

    if all_ledgers:
        trades_df = pd.concat(all_ledgers, ignore_index=True)
        trades_df.to_csv("expanded_trades.csv", index=False)
        print(f"Total trades across universe: {len(trades_df)}")
        
        # Output basic stats
        print("\n--- AGGREGATE RESULTS ---")
        print(f"Total PnL: {trades_df['net_pnl'].sum():.2f}")
        print(f"Win Rate:  {len(trades_df[trades_df['net_pnl']>0])/len(trades_df):.2%}")
        
        if not regime_df.empty:
            print("\n--- REGIME BREAKDOWN ---")
            print(trades_df.groupby("trend_regime")["net_pnl"].sum())
            
        print("\nRunning statistical and Monte Carlo analysis... (check reports generation next)")
    else:
        print("No trades generated.")


if __name__ == "__main__":
    run_expanded()
