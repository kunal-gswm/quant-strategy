import unittest
import numpy as np
import pandas as pd
from indicators.ema import wilder_style_ema
from indicators.rsi import wilder_rsi
from indicators.atr import wilder_atr
from execution.slippage import apply_slippage
from execution.cost_model import compute_trade_costs
from backtest.position import size_position
from data.validator import DataValidator
from strategy.trend_pullback import TrendPullbackStrategy

class DummyConfig:
    pass

class TestIndicators(unittest.TestCase):
    def test_ema(self):
        close = pd.Series([10, 10, 10, 20, 20])
        ema = wilder_style_ema(close, period=3)
        self.assertTrue(np.isnan(ema.iloc[0]))
        self.assertTrue(np.isnan(ema.iloc[1]))
        self.assertEqual(ema.iloc[2], 10.0)
        self.assertEqual(ema.iloc[3], 15.0)  # alpha = 2/4 = 0.5. 15.0
        self.assertEqual(ema.iloc[4], 17.5)

    def test_rsi(self):
        close = pd.Series([10, 12, 14, 16, 18, 20])
        rsi = wilder_rsi(close, period=3)
        # 10 to 12 (2), 12 to 14 (2), 14 to 16 (2) -> Avg Gain 2, Loss 0
        # Rsi should be 100 for purely gaining
        self.assertEqual(rsi.iloc[3], 100.0)

    def test_atr(self):
        df = pd.DataFrame({
            "high": [10, 12, 12, 12],
            "low": [8, 10, 10, 10],
            "close": [9, 11, 11, 11]
        })
        atr = wilder_atr(df, period=2)
        # Period 2 ATR is valid at index 2
        # TR1 = max(2, 3, 1) = 3 (from index 1, high 12, low 10, prev close 9)
        # TR2 = max(2, 1, 1) = 2
        # ATR2 = (3+2)/2 = 2.5
        self.assertEqual(atr.iloc[2], 2.5)

class TestExecution(unittest.TestCase):
    def test_position_sizing(self):
        qty = size_position(entry_price=100, stop_price=90, max_risk_rupees=1000, available_cash=5000)
        # Risk is 10 per share. Max risk 1000 -> 100 shares.
        # But max affordable is 5000 / 100 = 50 shares.
        self.assertEqual(qty, 50)
        
        qty2 = size_position(100, 95, 1000, 50000)
        # Risk 5. Max risk 1000 -> 200. Affordable 500.
        self.assertEqual(qty2, 200)

    def test_costs_and_slippage(self):
        price = apply_slippage(100.0, "buy", "fixed", 0.5)
        self.assertEqual(price, 100.5)
        
        price2 = apply_slippage(100.0, "sell", "fixed", 0.5)
        self.assertEqual(price2, 99.5)

        class Cfg:
            brokerage_type = "percentage"
            brokerage_value = 0.1
            exchange_transaction_charge_pct = 0.003
            stt_pct_delivery = 0.1
            sebi_charges_per_crore = 10.0
            stamp_duty_pct_buy_leg = 0.015
            gst_pct = 18.0

        c = compute_trade_costs(10000.0, 10500.0, Cfg())
        self.assertGreater(c, 0.0)

class TestDataValidator(unittest.TestCase):
    def test_invalid_ohlc(self):
        validator = DataValidator()
        df = pd.DataFrame({
            "open": [100, 100, -10],
            "high": [105, 90, 10],
            "low": [95, 80, 5],
            "close": [102, 95, 8],
            "volume": [1000, 1000, 1000]
        }, index=pd.date_range("2020-01-01", periods=3))
        clean, rej = validator.validate(df)
        self.assertEqual(len(clean), 1) # Only first row is valid. Row 2 high < open. Row 3 open is negative.
        self.assertEqual(len(rej), 2)

class TestStrategy(unittest.TestCase):
    def test_trend_pullback_signals(self):
        class Cfg:
            slope_bars = 1
            rsi_reclaim_level = 40
        strat = TrendPullbackStrategy(Cfg())
        df = pd.DataFrame({
            "ema50": [100, 101, 102],
            "close": [105, 105, 105],
            "rsi14": [50, 30, 45]
        })
        signals = strat.generate_signals(df)
        self.assertFalse(signals.iloc[0])
        self.assertFalse(signals.iloc[1])
        self.assertTrue(signals.iloc[2]) # ema > ema_prior, close > ema, rsi crossed 40

if __name__ == "__main__":
    unittest.main()
