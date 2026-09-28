# Signal Scanner & Dashboard Architecture Assessment

## 1. What Can Be Reused
- **Frozen Configuration:** `forward.config.get_frozen_forward_config()` provides all parameters without re-defining them.
- **Strategy Logic:** `strategy.trend_pullback.TrendPullbackStrategy.generate_signals()` can be reused directly to evaluate trend and RSI rules.
- **Indicators:** `wilder_style_ema`, `wilder_rsi`, `wilder_atr` from `indicators/` are reusable.
- **Data Validation:** Existing timestamp checks, NaT/NaN checks, and freshness evaluations in `forward.runner` can be abstracted.
- **Forward Engine:** `ForwardPaperEngine` logic to process signals into trades can remain intact.
- **Current Portfolios:** Existing CSV outputs in `results/forward/` can serve as the data layer for the dashboard.

## 2. What Needs to Be Added
- **`scanner/signal_schema.py`**: A structured schema (e.g. `dataclasses.dataclass`) to validate generated signals against required fields (e.g., `signal_id`, `data_freshness`).
- **`scanner/risk_calculator.py`**: A standalone component applying the 0.5% risk logic to compute `risk_per_share` and `position_size`.
- **`scanner/signal_scanner.py`**: The core component that ties data, strategy, and risk together, producing `VALID` / `INVALID` / `STALE` signals.
- **`dashboard/`**: Streamlit application reading `results/forward/*.csv` without writing or executing logic.

## 3. What Should NOT Be Changed
- The historical testing scripts in `research/`.
- The core strategy parameters (`TPQSE_v1.0`).
- The execution assumptions in the forward engine (e.g., next-day open slippage model).

## 4. Proposed Files & Folders
- `scanner/__init__.py`
- `scanner/signal_schema.py`
- `scanner/risk_calculator.py`
- `scanner/signal_scanner.py`
- `dashboard/app.py`
- `dashboard/data_loader.py`
- `dashboard/components.py`
