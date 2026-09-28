import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import math
import uuid
import json

import os

from forward_config import get_frozen_forward_config, STRATEGY_VERSION, UNIVERSE_NAME, SURVIVORSHIP_STATUS
from portfolio_engine import get_leg_cost

RESULTS_DIR = Path(os.environ.get("FORWARD_RESULTS_DIR", "d:/stratergy/results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR = RESULTS_DIR / "forward_universe_snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

FORWARD_START_TIMESTAMP = pd.to_datetime("2026-09-29")

class ForwardPaperEngine:
    def __init__(self, risk_pct: float = 0.005, max_positions: int = 10):
        self.cfg = get_frozen_forward_config()
        self.risk_pct = risk_pct
        self.max_positions = max_positions
        
        # Default state
        self.cash = self.cfg.starting_capital
        self.active_signals = []
        self.active_positions = []
        
        self.signals_log = []
        self.trades_log = []
        self.portfolio_history = []
        self.current_date = pd.to_datetime("1970-01-01")
        self._load_state()

    def _load_state(self):
        """Recover state from CSVs to allow uninterrupted restart."""
        if (RESULTS_DIR / "forward_signals.csv").exists():
            sigs = pd.read_csv(RESULTS_DIR / "forward_signals.csv").to_dict('records')
            self.signals_log = sigs
            # Active signals are those marked ENTRY_PENDING
            self.active_signals = [s for s in sigs if s["signal_status"] == "ENTRY_PENDING"]
            
        if (RESULTS_DIR / "forward_trades.csv").exists():
            self.trades_log = pd.read_csv(RESULTS_DIR / "forward_trades.csv").to_dict('records')
            
        if (RESULTS_DIR / "forward_portfolio_history.csv").exists():
            ph = pd.read_csv(RESULTS_DIR / "forward_portfolio_history.csv")
            if not ph.empty:
                self.portfolio_history = ph.to_dict('records')
                last_row = ph.iloc[-1]
                self.cash = float(last_row["cash"])
                self.current_date = pd.to_datetime(last_row["date"])
                
        # Recover open positions
        if (RESULTS_DIR / "forward_open_positions.json").exists():
            with open(RESULTS_DIR / "forward_open_positions.json", "r") as f:
                self.active_positions = json.load(f)

    def _save_state(self):
        with open(RESULTS_DIR / "forward_open_positions.json", "w") as f:
            json.dump(self.active_positions, f)

    def save_universe_snapshot(self, snapshot_date: pd.Timestamp, universe: list):
        """Save a dated snapshot of the universe used for this session."""
        records = []
        for u in universe:
            sym = u["symbol"] if isinstance(u, dict) else u
            records.append({
                "symbol": sym,
                "universe_version": UNIVERSE_NAME,
                "snapshot_timestamp": snapshot_date.strftime("%Y-%m-%d")
            })
        df = pd.DataFrame(records)
        path = SNAPSHOT_DIR / f"universe_{snapshot_date.strftime('%Y%m%d')}.csv"
        df.to_csv(path, index=False)

    def step(self, current_date: pd.Timestamp, day_data: dict, prev_day_data: dict = None):
        if current_date <= self.current_date:
            # Idempotent protection: Do not process the same or older dates twice
            return {"status": "SKIPPED", "reason": "Already processed"}
            
        if current_date < FORWARD_START_TIMESTAMP:
            return {"status": "SKIPPED", "reason": "Before launch"}
            
        self.current_date = current_date
        
        entries_executed = 0
        exits_executed = 0
        signals_generated = 0
        
        # 1. Execute Exits
        still_active = []
        for pos in self.active_positions:
            sym = pos["symbol"]
            if sym in day_data:
                bar = day_data[sym]
                
                hit_stop = bar["Low"] <= pos["stop_price"]
                hit_target = bar["High"] >= pos["target_price"]
                
                gap_stop = bar["Open"] <= pos["stop_price"]
                gap_target = bar["Open"] >= pos["target_price"]
                
                if gap_stop:
                    self._close_position(pos, bar["Open"], "STOP_GAP", current_date)
                    exits_executed += 1
                    continue
                elif gap_target:
                    self._close_position(pos, bar["Open"], "TARGET_GAP", current_date)
                    exits_executed += 1
                    continue
                
                if hit_stop and hit_target:
                    exit_price = pos["stop_price"] * (1 - self.cfg.execution.slippage_value / 100.0)
                    self._close_position(pos, exit_price, "STOP_SAME_BAR_AMBIGUITY", current_date)
                    exits_executed += 1
                    continue
                elif hit_stop:
                    exit_price = pos["stop_price"] * (1 - self.cfg.execution.slippage_value / 100.0)
                    self._close_position(pos, exit_price, "STOP", current_date)
                    exits_executed += 1
                    continue
                elif hit_target:
                    exit_price = pos["target_price"] * (1 - self.cfg.execution.slippage_value / 100.0)
                    self._close_position(pos, exit_price, "TARGET", current_date)
                    exits_executed += 1
                    continue
            
            if sym in day_data:
                pos["last_price"] = float(day_data[sym]["Close"])
            still_active.append(pos)
            
        self.active_positions = still_active
        
        market_value = sum(p["last_price"] * p["qty"] for p in self.active_positions)
        current_equity = self.cash + market_value
        
        # 2. Process Pending Signals
        remaining_signals = []
        for sig in self.active_signals:
            sym = sig["symbol"]
            if sym in day_data:
                bar = day_data[sym]
                entry_price = bar["Open"]
                
                slippage = entry_price * (self.cfg.execution.slippage_value / 100.0)
                actual_entry_price = entry_price + slippage
                
                risk_per_share = actual_entry_price - sig["planned_stop"]
                if risk_per_share > 0 and len(self.active_positions) < self.max_positions:
                    risk_budget = current_equity * self.risk_pct
                    qty = math.floor(risk_budget / risk_per_share)
                    
                    cost_est = qty * actual_entry_price
                    buy_cost = get_leg_cost(cost_est, True, self.cfg.cost_model)
                    
                    if qty > 0 and (cost_est + buy_cost) <= self.cash:
                        self.cash -= (cost_est + buy_cost)
                        
                        pos = {
                            "trade_id": sig["trade_id"],
                            "symbol": sym,
                            "signal_timestamp": sig["signal_timestamp"],
                            "entry_timestamp": current_date.strftime("%Y-%m-%d"),
                            "planned_entry": sig["planned_entry"],
                            "actual_entry": actual_entry_price,
                            "qty": qty,
                            "stop_price": sig["planned_stop"],
                            "target_price": sig["planned_target"],
                            "buy_cost": float(buy_cost),
                            "trade_value_buy": float(cost_est),
                            "last_price": float(bar["Close"]),
                            "initial_risk_rupees": float(risk_per_share * qty)
                        }
                        self.active_positions.append(pos)
                        sig["signal_status"] = "ENTERED"
                        entries_executed += 1
                    else:
                        sig["signal_status"] = "CANCELLED" # REJECTED_FUNDS
                else:
                    sig["signal_status"] = "CANCELLED" # REJECTED_RISK
                    
                self._update_signal_status(sig["trade_id"], sig["signal_status"])
            else:
                # Keep active if no data today
                remaining_signals.append(sig)
                
        self.active_signals = remaining_signals
        
        # 3. Generate New Signals
        if prev_day_data:
            for sym, data in prev_day_data.items():
                if data.get("signal") == True:
                    planned_entry = data["Close"] 
                    atr = data["ATR"]
                    stop = planned_entry - (atr * self.cfg.strategy.stop_atr_multiple)
                    target = planned_entry + (atr * self.cfg.strategy.reward_risk_multiple) * 1.5
                    
                    sig_time = pd.to_datetime(data["date"])
                    if sig_time >= FORWARD_START_TIMESTAMP:
                        t_id = f"{STRATEGY_VERSION}_{sym}_{sig_time.strftime('%Y%m%d')}"
                        
                        # Idempotent: check if already exists
                        if not any(s["trade_id"] == t_id for s in self.signals_log):
                            new_sig = {
                                "trade_id": t_id,
                                "symbol": sym,
                                "signal_timestamp": sig_time.strftime("%Y-%m-%d"),
                                "source_data_timestamp": sig_time.strftime("%Y-%m-%d"),
                                "strategy_version": STRATEGY_VERSION,
                                "EMA": float(data.get("EMA", 0)),
                                "EMA_slope": float(data.get("EMA_slope", 0)),
                                "RSI": float(data.get("RSI", 0)),
                                "ATR": float(atr),
                                "planned_entry": float(planned_entry),
                                "planned_stop": float(stop),
                                "planned_target": float(target),
                                "signal_status": "ENTRY_PENDING"
                            }
                            
                            self.active_signals.append(new_sig)
                            self.signals_log.append(new_sig)
                            self._append_csv("forward_signals.csv", [new_sig])
                            signals_generated += 1
        
        # 4. End of Day Accounting
        market_value_end = sum(p["last_price"] * p["qty"] for p in self.active_positions)
        unrealized_pnl = sum((p["last_price"] - p["actual_entry"]) * p["qty"] - p["buy_cost"] for p in self.active_positions)
        end_equity = self.cash + market_value_end
        gross_exposure = market_value_end / end_equity if end_equity > 0 else 0
        risk_exposure = sum(p["initial_risk_rupees"] for p in self.active_positions) / end_equity if end_equity > 0 else 0
        
        hist_row = {
            "date": current_date.strftime("%Y-%m-%d"),
            "cash": self.cash,
            "market_value": market_value_end,
            "equity": end_equity,
            "realized_pnl": 0.0, # Handled loosely, but we can compute daily change later if needed
            "unrealized_pnl": unrealized_pnl,
            "transaction_costs": 0.0,
            "daily_return": 0.0,
            "positions_open": len(self.active_positions),
            "gross_exposure": gross_exposure,
            "risk_exposure": risk_exposure,
            "drawdown": 0.0
        }
        self.portfolio_history.append(hist_row)
        self._append_csv("forward_portfolio_history.csv", [hist_row])
        self._save_state()
        
        return {
            "status": "SUCCESS",
            "signals_generated": signals_generated,
            "entries_executed": entries_executed,
            "exits_executed": exits_executed,
            "open_positions": len(self.active_positions),
            "ending_equity": end_equity
        }

    def _close_position(self, pos, exit_price, exit_reason, current_date):
        trade_value_sell = exit_price * pos["qty"]
        sell_cost = get_leg_cost(trade_value_sell, False, self.cfg.cost_model)
        
        net_proceeds = trade_value_sell - sell_cost
        self.cash += net_proceeds
        
        total_cost = pos["buy_cost"] + sell_cost
        gross_pnl = trade_value_sell - pos["trade_value_buy"]
        net_pnl = gross_pnl - total_cost
        
        r_mult = net_pnl / pos["initial_risk_rupees"] if pos["initial_risk_rupees"] > 0 else 0
        
        trade_record = {
            "trade_id": pos["trade_id"],
            "symbol": pos["symbol"],
            "strategy_version": STRATEGY_VERSION,
            "signal_timestamp": pos["signal_timestamp"],
            "entry_timestamp": pos["entry_timestamp"],
            "exit_timestamp": current_date.strftime("%Y-%m-%d"),
            "planned_entry": pos["planned_entry"],
            "actual_entry": pos["actual_entry"],
            "planned_stop": pos["stop_price"],
            "planned_target": pos["target_price"],
            "actual_exit": float(exit_price),
            "exit_reason": exit_reason,
            "quantity": pos["qty"],
            "initial_risk_rupees": pos["initial_risk_rupees"],
            "gross_pnl": float(gross_pnl),
            "transaction_costs": float(total_cost),
            "slippage_cost": float((pos["actual_entry"] - pos["planned_entry"]) * pos["qty"]),
            "net_pnl": float(net_pnl),
            "r_multiple": float(r_mult)
        }
        self.trades_log.append(trade_record)
        self._append_csv("forward_trades.csv", [trade_record])

    def _update_signal_status(self, trade_id, new_status):
        # We must rewrite the signals csv entirely to update status
        for s in self.signals_log:
            if s["trade_id"] == trade_id:
                s["signal_status"] = new_status
        pd.DataFrame(self.signals_log).to_csv(RESULTS_DIR / "forward_signals.csv", index=False)

    def _append_csv(self, filename, records):
        df = pd.DataFrame(records)
        path = RESULTS_DIR / filename
        df.to_csv(path, mode='a', header=not path.exists(), index=False)

def log_data_revision(symbol, original_date, original_val, revised_val):
    record = {
        "detected_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "affected_symbol": symbol,
        "affected_timestamp": original_date,
        "original_value": str(original_val),
        "revised_value": str(revised_val),
        "affected_field": "OHLCV",
        "action_taken": "LOGGED_ONLY"
    }
    df = pd.DataFrame([record])
    path = RESULTS_DIR / "forward_data_revisions.csv"
    df.to_csv(path, mode='a', header=not path.exists(), index=False)
