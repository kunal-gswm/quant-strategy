"""
Multi-stock backtest -- 5 year evaluation window.
Warm-up: 2019-01-01.  Eval: 2020-01-01 -> 2025-12-31.
"""

import pandas as pd
from data.loader import DataLoader
from data.validator import DataValidator
from indicators import ema, rsi, atr
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from metrics.performance import compute_core_metrics
from config import BacktestConfig

UNIVERSE = {
    "RELIANCE.NS":    "Large Cap",
    "TCS.NS":         "Large Cap",
    "PERSISTENT.NS":  "Mid Cap",
    "TRENT.NS":       "Mid Cap",
    "POLYCAB.NS":     "Mid Cap",
    "INDHOTEL.NS":    "Mid Cap",
    "DIXON.NS":       "Mid Cap",
    "CDSL.NS":        "Small Cap",
    "KPITTECH.NS":    "Small Cap",
    "ROUTE.NS":       "Small Cap",
}

LOAD_START = "2019-01-01"
EVAL_START = "2020-01-01"
EVAL_END   = "2025-12-31"


def run_single(symbol, config):
    loader = DataLoader()
    try:
        raw = loader.load(symbol, LOAD_START, EVAL_END)
    except Exception as e:
        print(f"  [ERROR] {symbol}: {e}")
        return pd.DataFrame(), {}, pd.DataFrame()

    if raw.empty or len(raw) < config.strategy.ema_period + 10:
        print(f"  [SKIP] {symbol}: not enough data ({len(raw)} bars)")
        return pd.DataFrame(), {}, pd.DataFrame()

    clean, rejects = DataValidator().validate(raw)
    if len(rejects):
        print(f"  [WARN] {symbol}: dropped {len(rejects)} invalid bars")

    clean["ema50"] = ema.wilder_style_ema(clean["close"], config.strategy.ema_period)
    clean["rsi14"] = rsi.wilder_rsi(clean["close"], config.strategy.rsi_period)
    clean["atr14"] = atr.wilder_atr(clean, config.strategy.atr_period)

    eval_df = clean.loc[EVAL_START:]
    if eval_df.empty:
        print(f"  [SKIP] {symbol}: no data in eval window")
        return pd.DataFrame(), {}, pd.DataFrame()

    print(f"  Bars: {len(clean)} total, {len(eval_df)} in eval window")

    strategy = TrendPullbackStrategy(config.strategy)
    engine = BacktestEngine(strategy=strategy, config=config)
    ledger_df, equity_curve = engine.run(eval_df, symbol=symbol)
    metrics = compute_core_metrics(ledger_df)
    return ledger_df, metrics, equity_curve


def main():
    config = BacktestConfig()
    all_results = []
    all_ledgers = []

    print("=" * 80)
    print(f"  MULTI-STOCK BACKTEST (5-YEAR)")
    print(f"  Warm-up from: {LOAD_START}  |  Eval: {EVAL_START} -> {EVAL_END}")
    print(f"  Capital per stock: {config.starting_capital:,.0f}")
    print("=" * 80)

    for symbol, cap in UNIVERSE.items():
        print(f"\n>> {symbol} ({cap})")
        ledger, metrics, equity = run_single(symbol, config)

        row = {
            "Symbol": symbol, "Cap": cap,
            "Trades": metrics.get("total_trades", 0),
            "Wins": 0, "Losses": 0,
            "Win Rate": None,
            "Gross Profit": 0, "Gross Loss": 0,
            "Net PnL": 0,
            "Profit Factor": None,
            "Expectancy": None,
        }
        if metrics:
            t = metrics.get("total_trades", 0)
            wr = metrics.get("win_rate", 0)
            row["Wins"] = int(round(t * wr))
            row["Losses"] = t - row["Wins"]
            row["Win Rate"] = wr
            row["Gross Profit"] = metrics.get("gross_profit", 0)
            row["Gross Loss"] = metrics.get("gross_loss", 0)
            row["Net PnL"] = metrics.get("net_pnl", 0)
            row["Profit Factor"] = metrics.get("profit_factor")
            row["Expectancy"] = metrics.get("expectancy")
            if t > 0:
                print(f"   Trades: {t}  |  W/L: {row['Wins']}/{row['Losses']}  |  "
                      f"Win Rate: {wr:.1%}  |  Net PnL: {row['Net PnL']:+,.2f}")
            else:
                print("   No trades generated.")
        if not ledger.empty:
            all_ledgers.append(ledger)
        all_results.append(row)

    summary = pd.DataFrame(all_results)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}" if pd.notna(x) else "-")

    print("\n" + "=" * 80)
    print("  SUMMARY BY STOCK")
    print("=" * 80)
    cols = ["Symbol", "Cap", "Trades", "Wins", "Losses", "Win Rate", "Net PnL", "Profit Factor"]
    print(summary[cols].to_string(index=False))

    print(f"\n{'=' * 80}")
    print("  SUMMARY BY MARKET CAP")
    print(f"{'=' * 80}")
    cap_agg = summary.groupby("Cap").agg(
        Stocks=("Symbol", "count"),
        Total_Trades=("Trades", "sum"),
        Total_PnL=("Net PnL", "sum"),
    ).reset_index()
    print(cap_agg.to_string(index=False))

    total_pnl = summary["Net PnL"].sum()
    total_trades = int(summary["Trades"].sum())
    total_wins = int(summary["Wins"].sum())
    profitable = int((summary["Net PnL"] > 0).sum())

    print(f"\n{'=' * 80}")
    print(f"  PORTFOLIO TOTAL")
    print(f"  Trades: {total_trades}  |  Wins: {total_wins}/{total_trades}  |  "
          f"Net PnL: {total_pnl:+,.2f}")
    print(f"  Profitable stocks: {profitable}/{len(UNIVERSE)}")
    print(f"{'=' * 80}")

    if all_ledgers:
        combined = pd.concat(all_ledgers, ignore_index=True)
        combined.to_csv("multi_stock_5yr_trades.csv", index=False)
        print(f"\n  Trade log saved -> multi_stock_5yr_trades.csv ({len(combined)} trades)")
        print(f"\n{'-' * 80}")
        print("  ALL TRADES (detail)")
        print(f"{'-' * 80}")
        detail = ["symbol", "signal_timestamp", "entry_timestamp", "exit_timestamp",
                   "entry_price", "exit_price", "quantity", "net_pnl", "r_multiple", "exit_reason"]
        print(combined[detail].to_string(index=False))
    else:
        print("\n  No trades generated across any stock.")
    print()


if __name__ == "__main__":
    main()
