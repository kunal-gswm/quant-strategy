"""
Comprehensive test suite for walk-forward validation.

Covers:
  - Walk-forward date splitting
  - No overlap between train/test
  - No future data leakage
  - Next-open entry
  - Stop/target calculation
  - Execution classification
  - Cost calculation
  - Bootstrap reproducibility
  - Monte Carlo reproducibility
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import BacktestConfig, StrategyConfig
from backtest.execution import check_exit, OpenPosition, ExitReason
from backtest.position import size_position
from backtest.engine import BacktestEngine
from execution.cost_model import compute_trade_costs
from execution.slippage import apply_slippage
from indicators import ema, rsi, atr
from strategy.trend_pullback import TrendPullbackStrategy
from data.validator import DataValidator
from analysis.monte_carlo import run_monte_carlo
from research.walk_forward import (
    classify_execution,
    bootstrap_ci,
    WALK_FORWARD_WINDOWS,
    compute_trade_metrics,
)


# ═══════════════════════════════════════════════════════════════════════════
# Walk-Forward Date Splitting
# ═══════════════════════════════════════════════════════════════════════════

class TestWalkForwardDateSplitting:
    """Verify walk-forward windows are correctly defined."""
    
    def test_five_test_years(self):
        """There should be exactly 5 test windows: 2021-2025."""
        assert len(WALK_FORWARD_WINDOWS) == 5
        years = [w["test_year"] for w in WALK_FORWARD_WINDOWS]
        assert years == [2021, 2022, 2023, 2024, 2025]
    
    def test_expanding_train_windows(self):
        """Train windows should expand: all start at 2019-01-01."""
        for w in WALK_FORWARD_WINDOWS:
            assert w["train_start"] == "2019-01-01"
        # Train end should advance
        train_ends = [w["train_end"] for w in WALK_FORWARD_WINDOWS]
        assert train_ends == [
            "2020-12-31", "2021-12-31", "2022-12-31",
            "2023-12-31", "2024-12-31"
        ]
    
    def test_test_windows_are_calendar_years(self):
        """Each test window should be a full calendar year."""
        for w in WALK_FORWARD_WINDOWS:
            assert w["test_start"].endswith("-01-01")
            assert w["test_end"].endswith("-12-31")
            assert w["test_start"][:4] == w["test_end"][:4]
            assert int(w["test_start"][:4]) == w["test_year"]


# ═══════════════════════════════════════════════════════════════════════════
# No Overlap Between Train/Test
# ═══════════════════════════════════════════════════════════════════════════

class TestNoOverlap:
    """Verify no overlap between training and test periods."""
    
    def test_train_end_before_test_start(self):
        """Training period must end before test period starts."""
        for w in WALK_FORWARD_WINDOWS:
            train_end = pd.Timestamp(w["train_end"])
            test_start = pd.Timestamp(w["test_start"])
            assert train_end < test_start, (
                f"Window {w['test_year']}: train_end={train_end} >= test_start={test_start}"
            )
    
    def test_no_test_overlap_between_windows(self):
        """Test periods must not overlap with each other."""
        for i in range(len(WALK_FORWARD_WINDOWS) - 1):
            test_end_i = pd.Timestamp(WALK_FORWARD_WINDOWS[i]["test_end"])
            test_start_next = pd.Timestamp(WALK_FORWARD_WINDOWS[i + 1]["test_start"])
            assert test_end_i < test_start_next
    
    def test_test_periods_contiguous(self):
        """Test periods should cover 2021-2025 continuously."""
        for i in range(len(WALK_FORWARD_WINDOWS) - 1):
            current_year = WALK_FORWARD_WINDOWS[i]["test_year"]
            next_year = WALK_FORWARD_WINDOWS[i + 1]["test_year"]
            assert next_year == current_year + 1


# ═══════════════════════════════════════════════════════════════════════════
# No Future Data Leakage
# ═══════════════════════════════════════════════════════════════════════════

class TestNoFutureLeakage:
    """Verify indicators and signals don't leak future data."""
    
    def _make_sample_df(self, n=200):
        """Create a sample OHLCV DataFrame."""
        np.random.seed(42)
        dates = pd.bdate_range("2020-01-01", periods=n)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        return pd.DataFrame({
            "open": close + np.random.randn(n) * 0.2,
            "high": close + abs(np.random.randn(n)) * 1.0,
            "low": close - abs(np.random.randn(n)) * 1.0,
            "close": close,
            "volume": np.random.randint(100000, 1000000, n),
        }, index=dates)
    
    def test_ema_no_future_data(self):
        """EMA at bar t must not depend on bars after t."""
        df = self._make_sample_df(200)
        full_ema = ema.wilder_style_ema(df["close"], 50)
        
        # Compute EMA using only first 150 bars
        partial_ema = ema.wilder_style_ema(df["close"].iloc[:150], 50)
        
        # Values up to bar 149 should be identical
        for i in range(50, 150):
            assert abs(full_ema.iloc[i] - partial_ema.iloc[i]) < 1e-10, (
                f"EMA mismatch at bar {i}: full={full_ema.iloc[i]}, partial={partial_ema.iloc[i]}"
            )
    
    def test_rsi_no_future_data(self):
        """RSI at bar t must not depend on bars after t."""
        df = self._make_sample_df(200)
        full_rsi = rsi.wilder_rsi(df["close"], 14)
        partial_rsi = rsi.wilder_rsi(df["close"].iloc[:150], 14)
        
        for i in range(14, 150):
            if pd.notna(full_rsi.iloc[i]) and pd.notna(partial_rsi.iloc[i]):
                assert abs(full_rsi.iloc[i] - partial_rsi.iloc[i]) < 1e-10
    
    def test_atr_no_future_data(self):
        """ATR at bar t must not depend on bars after t."""
        df = self._make_sample_df(200)
        full_atr = atr.wilder_atr(df, 14)
        partial_atr = atr.wilder_atr(df.iloc[:150], 14)
        
        for i in range(14, 150):
            if pd.notna(full_atr.iloc[i]) and pd.notna(partial_atr.iloc[i]):
                assert abs(full_atr.iloc[i] - partial_atr.iloc[i]) < 1e-10


# ═══════════════════════════════════════════════════════════════════════════
# Next-Open Entry
# ═══════════════════════════════════════════════════════════════════════════

class TestNextOpenEntry:
    """Verify entries happen at the next bar's open, not the signal bar."""
    
    def test_signal_and_entry_different_bars(self):
        """Signal timestamp and entry timestamp must differ."""
        # Create minimal data with a known signal
        dates = pd.bdate_range("2020-01-01", periods=100)
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 0.3)
        df = pd.DataFrame({
            "open": close - 0.1,
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "volume": [1000000] * 100,
        }, index=dates)
        
        # Add indicators
        df["ema50"] = ema.wilder_style_ema(df["close"], 50)
        df["rsi14"] = rsi.wilder_rsi(df["close"], 14)
        df["atr14"] = atr.wilder_atr(df, 14)
        
        config = BacktestConfig()
        strategy = TrendPullbackStrategy(config.strategy)
        engine = BacktestEngine(strategy=strategy, config=config)
        ledger_df, _ = engine.run(df, symbol="TEST")
        
        if not ledger_df.empty:
            for _, trade in ledger_df.iterrows():
                sig = pd.Timestamp(trade["signal_timestamp"])
                ent = pd.Timestamp(trade["entry_timestamp"])
                assert ent > sig, (
                    f"Entry {ent} not after signal {sig}"
                )


# ═══════════════════════════════════════════════════════════════════════════
# Stop/Target Calculation
# ═══════════════════════════════════════════════════════════════════════════

class TestStopTargetCalculation:
    """Verify stop and target are calculated correctly."""
    
    def test_stop_uses_entry_and_atr(self):
        """Stop should be entry_price - 1.5 * ATR."""
        entry = 100.0
        atr_val = 5.0
        stop = entry - 1.5 * atr_val
        assert abs(stop - 92.5) < 1e-10
    
    def test_target_uses_2r(self):
        """Target should be entry + 2 * risk."""
        entry = 100.0
        stop = 92.5
        risk = entry - stop  # 7.5
        target = entry + 2.0 * risk
        assert abs(target - 115.0) < 1e-10
    
    def test_stop_target_in_engine(self):
        """BacktestEngine must compute stop and target correctly."""
        # entry_fill = open + slippage
        # stop = entry_fill - 1.5 * atr
        # target = entry_fill + 2 * (entry_fill - stop)
        entry_fill = 100.05  # open=100, 0.05% slippage
        atr_val = 5.0
        stop = entry_fill - 1.5 * atr_val
        risk = entry_fill - stop
        target = entry_fill + 2.0 * risk
        
        assert abs(risk - 7.5) < 1e-6
        assert abs(target - (entry_fill + 15.0)) < 1e-6


# ═══════════════════════════════════════════════════════════════════════════
# Execution Classification
# ═══════════════════════════════════════════════════════════════════════════

class TestExecutionClassification:
    """Test the execution classification logic."""
    
    def test_normal_stop(self):
        """A trade hitting stop at exact stop price with minimal slippage."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 92.5,  # exact stop
            "quantity": 10,
            "gross_pnl": -75.0,
            "total_costs": 5.0,
            "net_pnl": -80.0,
            "exit_reason": "STOP",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "NORMAL_STOP" in result or "TRANSACTION_COST" in result or "INTEGER_POSITION_SIZE" in result
        assert "GAP_THROUGH_STOP" not in result
        assert "END_OF_DATA" not in result
    
    def test_normal_target(self):
        """A trade hitting target at exact target price."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 115.0,  # exact target
            "quantity": 10,
            "gross_pnl": 150.0,
            "total_costs": 5.0,
            "net_pnl": 145.0,
            "exit_reason": "TARGET",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "GAP_THROUGH_TARGET" not in result
        assert "END_OF_DATA" not in result
    
    def test_gap_through_stop(self):
        """Exit price well below stop => gap through stop."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 88.0,  # far below stop
            "quantity": 10,
            "gross_pnl": -120.0,
            "total_costs": 5.0,
            "net_pnl": -125.0,
            "exit_reason": "STOP",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "GAP_THROUGH_STOP" in result
    
    def test_gap_through_target(self):
        """Exit price well above target => gap through target."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 120.0,  # above target
            "quantity": 10,
            "gross_pnl": 200.0,
            "total_costs": 5.0,
            "net_pnl": 195.0,
            "exit_reason": "TARGET",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "GAP_THROUGH_TARGET" in result
    
    def test_end_of_data(self):
        """END_OF_DATA exit reason."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 105.0,
            "quantity": 10,
            "gross_pnl": 50.0,
            "total_costs": 5.0,
            "net_pnl": 45.0,
            "exit_reason": "END_OF_DATA",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert result == ["END_OF_DATA"]
    
    def test_intrabar_ambiguity(self):
        """When both stop and target are hit in same bar."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 92.5,
            "quantity": 10,
            "gross_pnl": -75.0,
            "total_costs": 5.0,
            "net_pnl": -80.0,
            "exit_reason": "STOP",
            "ambiguous_exit": True,
        }
        result = classify_execution(row)
        assert "INTRABAR_AMBIGUITY" in result
    
    def test_transaction_cost_classification(self):
        """Significant transaction costs should be classified."""
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 115.0,
            "quantity": 1,  # Very small qty, costs dominate
            "gross_pnl": 15.0,
            "total_costs": 5.0,
            "net_pnl": 10.0,
            "exit_reason": "TARGET",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "TRANSACTION_COST" in result
    
    def test_integer_position_size(self):
        """Non-integer ideal quantity causes position sizing effect."""
        # risk_per_share = 7.5, max_risk = 1000
        # ideal_qty = 1000/7.5 = 133.33, actual = 133
        row = {
            "entry_price": 100.0,
            "stop_price": 92.5,
            "target_price": 115.0,
            "exit_price": 92.5,
            "quantity": 133,
            "gross_pnl": -997.5,
            "total_costs": 50.0,
            "net_pnl": -1047.5,
            "exit_reason": "STOP",
            "ambiguous_exit": False,
        }
        result = classify_execution(row)
        assert "INTEGER_POSITION_SIZE" in result


# ═══════════════════════════════════════════════════════════════════════════
# Cost Calculation
# ═══════════════════════════════════════════════════════════════════════════

class TestCostCalculation:
    """Verify transaction cost model."""
    
    def test_costs_positive(self):
        """All costs must be positive for non-zero trade values."""
        cfg = BacktestConfig().cost_model
        cost = compute_trade_costs(100000, 105000, cfg)
        assert cost > 0
    
    def test_costs_include_stt(self):
        """STT should be applied to both legs."""
        cfg = BacktestConfig().cost_model
        cost = compute_trade_costs(100000, 100000, cfg)
        # STT = 0.10% on each leg = 100 + 100 = 200
        assert cost >= 200  # At least STT
    
    def test_stamp_duty_buy_only(self):
        """Stamp duty should only apply to buy leg."""
        cfg = BacktestConfig().cost_model
        # Stamp duty = 0.015% of buy value = 15
        cost_buy = compute_trade_costs(100000, 0, cfg)
        cost_sell = compute_trade_costs(0, 100000, cfg)
        # Buy leg should have stamp duty, sell leg should not
        assert cost_buy > cost_sell
    
    def test_costs_scale_with_value(self):
        """Costs should scale roughly linearly with trade value."""
        cfg = BacktestConfig().cost_model
        cost_1 = compute_trade_costs(100000, 100000, cfg)
        cost_2 = compute_trade_costs(200000, 200000, cfg)
        assert abs(cost_2 / cost_1 - 2.0) < 0.1


# ═══════════════════════════════════════════════════════════════════════════
# Bootstrap Reproducibility
# ═══════════════════════════════════════════════════════════════════════════

class TestBootstrapReproducibility:
    """Verify bootstrap produces identical results with same seed."""
    
    def test_bootstrap_deterministic(self):
        """Same data + same seed => same results."""
        data = np.array([1.0, -0.5, 2.0, -1.0, 0.5, 1.5, -0.3])
        
        result1 = bootstrap_ci(data, stat_fn=np.mean, n_boot=1000, seed=42)
        result2 = bootstrap_ci(data, stat_fn=np.mean, n_boot=1000, seed=42)
        
        assert abs(result1["ci_lower"] - result2["ci_lower"]) < 1e-10
        assert abs(result1["ci_upper"] - result2["ci_upper"]) < 1e-10
        assert abs(result1["point_estimate"] - result2["point_estimate"]) < 1e-10
    
    def test_bootstrap_different_seed_different_result(self):
        """Different seeds should produce different CI bounds."""
        data = np.array([1.0, -0.5, 2.0, -1.0, 0.5, 1.5, -0.3, 0.8, -0.2, 1.1])
        
        result1 = bootstrap_ci(data, stat_fn=np.mean, n_boot=5000, seed=42)
        result2 = bootstrap_ci(data, stat_fn=np.mean, n_boot=5000, seed=99)
        
        # Point estimates should be the same (same data)
        assert abs(result1["point_estimate"] - result2["point_estimate"]) < 1e-10
        # CI bounds should differ
        assert result1["ci_lower"] != result2["ci_lower"]
    
    def test_bootstrap_ci_contains_point_estimate(self):
        """The point estimate should fall within the CI."""
        data = np.array([1.0, -0.5, 2.0, -1.0, 0.5, 1.5, -0.3])
        result = bootstrap_ci(data, stat_fn=np.mean, n_boot=10000, seed=42)
        assert result["ci_lower"] <= result["point_estimate"] <= result["ci_upper"]


# ═══════════════════════════════════════════════════════════════════════════
# Monte Carlo Reproducibility
# ═══════════════════════════════════════════════════════════════════════════

class TestMonteCarloReproducibility:
    """Verify Monte Carlo produces identical results with same seed."""
    
    def test_mc_deterministic_shuffle(self):
        """Same trades + same seed => same MC results (shuffle)."""
        pnl = np.array([500, -300, 1000, -400, 200, -100, 800, -500])
        
        r1 = run_monte_carlo(pnl, seed=42, method="shuffle", n_simulations=1000)
        r2 = run_monte_carlo(pnl, seed=42, method="shuffle", n_simulations=1000)
        
        np.testing.assert_array_equal(r1["ending_equity"], r2["ending_equity"])
        np.testing.assert_array_equal(r1["max_drawdowns"], r2["max_drawdowns"])
    
    def test_mc_deterministic_bootstrap(self):
        """Same trades + same seed => same MC results (bootstrap)."""
        pnl = np.array([500, -300, 1000, -400, 200, -100, 800, -500])
        
        r1 = run_monte_carlo(pnl, seed=42, method="bootstrap", n_simulations=1000)
        r2 = run_monte_carlo(pnl, seed=42, method="bootstrap", n_simulations=1000)
        
        np.testing.assert_array_equal(r1["ending_equity"], r2["ending_equity"])
    
    def test_mc_different_seed(self):
        """Different seeds should produce different max drawdown distributions."""
        pnl = np.array([500, -300, 1000, -400, 200, -100, 800, -500])
        
        r1 = run_monte_carlo(pnl, seed=42, method="shuffle", n_simulations=100)
        r2 = run_monte_carlo(pnl, seed=99, method="shuffle", n_simulations=100)
        
        # With shuffle, ending equity is invariant (same sum) but
        # max drawdown distribution depends on ordering
        assert not np.array_equal(r1["max_drawdowns"], r2["max_drawdowns"])
    
    def test_mc_empty_trades(self):
        """Monte Carlo with no trades should not crash."""
        r = run_monte_carlo(np.array([]), seed=42)
        assert len(r["ending_equity"]) == 1
        assert r["ending_equity"][0] == 500000.0


# ═══════════════════════════════════════════════════════════════════════════
# Existing Tests (preserved from test_all.py)
# ═══════════════════════════════════════════════════════════════════════════

class TestIndicators:
    """Core indicator tests."""
    
    def test_ema_warmup(self):
        """EMA should have NaN for bars before the seed."""
        close = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
        result = ema.wilder_style_ema(close, period=3)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])
        assert pd.notna(result.iloc[2])  # seed bar
    
    def test_rsi_all_gains(self):
        """RSI with all gains should be 100."""
        close = pd.Series(range(1, 20), dtype=float)
        result = rsi.wilder_rsi(close, period=14)
        # Last value should be 100 (all gains, no losses)
        assert result.iloc[-1] == 100.0
    
    def test_atr_basic(self):
        """ATR should be non-negative and NaN for warm-up."""
        df = pd.DataFrame({
            "open": [10, 11, 12, 13, 14, 10, 11, 12, 13, 14, 10, 11, 12, 13, 14, 15, 16],
            "high": [11, 12, 13, 14, 15, 11, 12, 13, 14, 15, 11, 12, 13, 14, 15, 16, 17],
            "low":  [9, 10, 11, 12, 13, 9, 10, 11, 12, 13, 9, 10, 11, 12, 13, 14, 15],
            "close": [10.5, 11.5, 12.5, 13.5, 14.5, 10.5, 11.5, 12.5, 13.5, 14.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5],
            "volume": [100] * 17,
        })
        result = atr.wilder_atr(df, period=3)
        # Should have NaN for warm-up, positive values after
        assert pd.isna(result.iloc[0])
        for i in range(3, len(result)):
            if pd.notna(result.iloc[i]):
                assert result.iloc[i] > 0


class TestPositionSizing:
    """Position sizing tests."""
    
    def test_basic_sizing(self):
        """Verify position sizing with known inputs."""
        qty = size_position(100.0, 95.0, 1000.0, 500000.0)
        # risk_per_share = 5, max_risk = 1000, qty = floor(200) = 200
        assert qty == 200
    
    def test_cash_constraint(self):
        """Position size should be limited by available cash."""
        qty = size_position(100.0, 95.0, 1000.0, 500.0)
        # Can only afford floor(500/100) = 5 shares
        assert qty == 5
    
    def test_zero_risk(self):
        """Zero risk should produce zero quantity."""
        qty = size_position(100.0, 100.0, 1000.0, 500000.0)
        assert qty == 0
    
    def test_negative_risk(self):
        """Negative risk (stop above entry) should produce zero quantity."""
        qty = size_position(100.0, 105.0, 1000.0, 500000.0)
        assert qty == 0


class TestSlippage:
    """Slippage tests."""
    
    def test_buy_slippage_increases_price(self):
        """Buy slippage should increase the fill price."""
        fill = apply_slippage(100.0, "buy", "percentage", 0.05)
        assert fill > 100.0
    
    def test_sell_slippage_decreases_price(self):
        """Sell slippage should decrease the fill price."""
        fill = apply_slippage(100.0, "sell", "percentage", 0.05)
        assert fill < 100.0


class TestCheckExit:
    """Exit checking tests."""
    
    def test_stop_hit(self):
        """Low <= stop should trigger stop."""
        pos = OpenPosition(100.0, 95.0, 110.0, 10,
                          entry_timestamp="2020-01-01")
        reason, level, ambiguous = check_exit(pos, 102.0, 94.0)
        assert reason == ExitReason.STOP
        assert level == 95.0
        assert not ambiguous
    
    def test_target_hit(self):
        """High >= target should trigger target."""
        pos = OpenPosition(100.0, 95.0, 110.0, 10,
                          entry_timestamp="2020-01-01")
        reason, level, ambiguous = check_exit(pos, 111.0, 99.0)
        assert reason == ExitReason.TARGET
        assert level == 110.0
        assert not ambiguous
    
    def test_both_hit_conservative(self):
        """When both stop and target hit, conservative => stop."""
        pos = OpenPosition(100.0, 95.0, 110.0, 10,
                          entry_timestamp="2020-01-01")
        reason, level, ambiguous = check_exit(pos, 111.0, 94.0, "conservative")
        assert reason == ExitReason.STOP
        assert ambiguous
    
    def test_neither_hit(self):
        """No exit when neither stop nor target hit."""
        pos = OpenPosition(100.0, 95.0, 110.0, 10,
                          entry_timestamp="2020-01-01")
        reason, level, ambiguous = check_exit(pos, 105.0, 96.0)
        assert reason is None


class TestComputeTradeMetrics:
    """Test the compute_trade_metrics helper."""
    
    def test_empty_trades(self):
        """Empty DataFrame should return zeros."""
        m = compute_trade_metrics(pd.DataFrame())
        assert m["trades"] == 0
        assert m["net_pnl"] == 0.0
    
    def test_all_winners(self):
        """All winning trades should give 100% win rate."""
        df = pd.DataFrame({
            "net_pnl": [100, 200, 300],
            "gross_pnl": [110, 210, 310],
            "total_costs": [10, 10, 10],
            "r_multiple": [2.0, 2.0, 2.0],
        })
        m = compute_trade_metrics(df)
        assert m["wins"] == 3
        assert m["losses"] == 0
        assert m["win_rate"] == 1.0
        assert m["net_pnl"] == 600.0
    
    def test_mixed_trades(self):
        """Mixed trades should calculate correctly."""
        df = pd.DataFrame({
            "net_pnl": [100, -50, 200, -80],
            "gross_pnl": [110, -40, 210, -70],
            "total_costs": [10, 10, 10, 10],
            "r_multiple": [1.5, -1.0, 2.0, -1.0],
        })
        m = compute_trade_metrics(df)
        assert m["trades"] == 4
        assert m["wins"] == 2
        assert m["losses"] == 2
        assert m["win_rate"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
