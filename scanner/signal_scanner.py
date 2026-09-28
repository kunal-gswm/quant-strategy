import pandas as pd
import numpy as np
from datetime import datetime
from strategy.trend_pullback import TrendPullbackStrategy
from forward.config import get_frozen_forward_config, STRATEGY_VERSION
from indicators.ema import wilder_style_ema
from indicators.rsi import wilder_rsi
from indicators.atr import wilder_atr
from scanner.signal_schema import Signal
from scanner.risk_calculator import RiskCalculator

class SignalScanner:
    def __init__(self, current_date: pd.Timestamp, equity: float = 1_000_000.0, risk_percent: float = 0.005):
        self.current_date = current_date
        self.cfg = get_frozen_forward_config()
        self.strategy = TrendPullbackStrategy(self.cfg.strategy)
        self.risk_calc = RiskCalculator(risk_percent=risk_percent)
        self.equity = equity

    def scan_symbol(self, symbol: str, df: pd.DataFrame, max_data_ts: pd.Timestamp, expected_delay: bool) -> Signal:
        """
        Scans a single symbol's DataFrame for a valid signal on current_date.
        """
        if df.empty or len(df) < max(self.cfg.strategy.ema_period, self.cfg.strategy.rsi_period) + self.cfg.strategy.slope_bars:
            return None # Insufficient data

        df = df.copy()
        
        # Ensure column names for indicators
        df_lower = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        
        # Calculate indicators expected by strategy
        df_lower["ema50"] = wilder_style_ema(df_lower["close"], self.cfg.strategy.ema_period)
        df_lower["rsi14"] = wilder_rsi(df_lower["close"], self.cfg.strategy.rsi_period)
        df_lower["atr"] = wilder_atr(df_lower, self.cfg.strategy.atr_period)

        # Drop NaN to ensure we are only working with valid indicator periods
        # Actually wait, strategy expects NaNs to be present to shift correctly if we just pass the whole thing
        # But we must only generate signal on the requested current_date
        
        signals = self.strategy.generate_signals(df_lower)
        df_lower["signal"] = signals

        # We are only interested in a signal generated on the current date
        if self.current_date not in df_lower.index:
            return None
        
        row = df_lower.loc[self.current_date]
        if not row["signal"]:
            return None

        # We have a mathematical signal, now validate safety and risk
        # Freshness Check
        data_ts = self.current_date
        execution_timestamp = pd.Timestamp.now()
        data_age_hours = (execution_timestamp.normalize() - data_ts).total_seconds() / 3600.0
        
        if data_age_hours > 24 and not expected_delay:
            data_freshness = "STALE"
            status = "STALE"
        else:
            data_freshness = "FRESH"
            status = "VALID"

        # Signal properties
        planned_entry = float(row["close"])
        atr = float(row["atr"])
        stop_loss = planned_entry - (atr * self.cfg.strategy.stop_atr_multiple)
        target = planned_entry + (atr * self.cfg.strategy.reward_risk_multiple) * 1.5

        # Format ID
        sig_id = f"{STRATEGY_VERSION}_{symbol}_{self.current_date.strftime('%Y%m%d')}"

        # Risk calculation
        risk_res = self.risk_calc.calculate_position(self.equity, planned_entry, stop_loss)
        if risk_res["status"] != "VALID" and status == "VALID":
            status = "INVALID"
            
        ema_prior = float(df_lower["ema50"].shift(self.cfg.strategy.slope_bars).loc[self.current_date])
        trend_slope = float(row["ema50"]) - ema_prior
        
        reason = []
        if trend_slope > 0: reason.append("EMA50 slope positive")
        if row["close"] > row["ema50"]: reason.append("Price above EMA50")
        reason.append("RSI crossed above 40")
        if status != "VALID":
            reason.append(f"Rejected: {status}")

        signal = Signal(
            strategy_version=STRATEGY_VERSION,
            signal_id=sig_id,
            symbol=symbol,
            signal_timestamp=self.current_date.strftime("%Y-%m-%d"),
            direction="LONG",
            signal_price=planned_entry,
            planned_entry=planned_entry,
            stop_loss=stop_loss,
            target=target,
            risk_per_share=risk_res["risk_per_share"],
            reward_per_share=(target - planned_entry),
            risk_reward_ratio=(target - planned_entry) / risk_res["risk_per_share"] if risk_res["risk_per_share"] > 0 else 0,
            atr=atr,
            ema50=float(row["ema50"]),
            rsi14=float(row["rsi14"]),
            trend_slope=trend_slope,
            position_size=risk_res["position_size"],
            capital_at_risk=risk_res["risk_amount"],
            risk_percent=self.risk_calc.risk_percent,
            data_timestamp=self.current_date.strftime("%Y-%m-%d"),
            data_freshness=data_freshness,
            signal_status=status,
            signal_reason=" | ".join(reason)
        )
        return signal

    def scan_universe(self, universe_data: dict, expected_delay: bool) -> list:
        signals = []
        # Find max timestamp across all valid data
        max_ts = pd.Timestamp("1970-01-01")
        for sym, df in universe_data.items():
            if not df.empty:
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                if df.index[-1] > max_ts:
                    max_ts = df.index[-1]

        for sym, df in universe_data.items():
            sig = self.scan_symbol(sym, df, max_ts, expected_delay)
            if sig:
                signals.append(sig)
        return signals
