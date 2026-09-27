import pandas as pd
from data.loader import DataLoader
from data.validator import DataValidator
from indicators import ema, rsi, atr
from strategy.trend_pullback import TrendPullbackStrategy
from backtest.engine import BacktestEngine
from metrics.performance import compute_core_metrics
from config import BacktestConfig

def run_backtest(symbol: str, start: str, end: str, config: BacktestConfig):
    try:
        raw = DataLoader().load(symbol, start, end)
    except NotImplementedError:
        print("Using dummy data as DataLoader is a stub")
        dates = pd.date_range(start, periods=200, freq="D")
        import numpy as np
        np.random.seed(42)
        closes = 100 + np.random.randn(200).cumsum()
        raw = pd.DataFrame({
            "open": closes + np.random.randn(200) * 0.5,
            "high": closes + np.abs(np.random.randn(200)),
            "low": closes - np.abs(np.random.randn(200)),
            "close": closes,
            "volume": 1000
        }, index=dates)

    clean, rejections = DataValidator().validate(raw)
    
    clean["ema50"] = ema.wilder_style_ema(clean["close"], config.strategy.ema_period)
    clean["rsi14"] = rsi.wilder_rsi(clean["close"], config.strategy.rsi_period)
    clean["atr14"] = atr.wilder_atr(clean, config.strategy.atr_period)
    
    strategy = TrendPullbackStrategy(config.strategy)
    engine = BacktestEngine(strategy=strategy, config=config)
    ledger_df, equity_curve = engine.run(clean)
    
    metrics = compute_core_metrics(ledger_df)
    
    return ledger_df, metrics, equity_curve

if __name__ == "__main__":
    config = BacktestConfig()
    ledger, metrics, equity = run_backtest("DUMMY", "2020-01-01", "2020-12-31", config)
    print("Metrics:")
    import pprint
    pprint.pprint(metrics)
    print("\nLedger:")
    print(ledger)
