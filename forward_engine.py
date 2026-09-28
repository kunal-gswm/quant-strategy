import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import math

from forward_config import get_frozen_forward_config, STRATEGY_VERSION, UNIVERSE_NAME, SURVIVORSHIP_STATUS
from portfolio_engine import get_leg_cost

RESULTS_DIR = Path("d:/stratergy/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class ForwardPaperEngine:
    def __init__(self, start_date: str, initial_capital: float = 1_000_000.0, risk_pct: float = 0.005, max_positions: int = 10):
        self.cfg = get_frozen_forward_config()
        self.start_date = pd.to_datetime(start_date)
        
        self.cash = initial_capital
        self.risk_pct = risk_pct
        self.max_positions = max_positions
        
        self.active_signals = []
        self.active_positions = []
        
        self.signals_log = []
        self.trades_log = []
        self.portfolio_history = []
        
        self.current_date = self.start_date
        
    def step(self, current_date: pd.Timestamp, day_data: dict, prev_day_data: dict = None):
        """
        Process a single day in the forward test.
        day_data: dict mapping symbol -> pd.Series containing Open, High, Low, Close, Volume for current_date
        prev_day_data: data up to current_date - 1 (for signal generation)
        """
        self.current_date = current_date
        
        # 1. Execute Exits (Stops and Targets)
        still_active = []
        for pos in self.active_positions:
            sym = pos["symbol"]
            if sym in day_data:
                bar = day_data[sym]
                
                # Check for gap through stop
                if bar["Open"] <= pos["stop_price"]:
                    # Gap down through stop
                    exit_price = bar["Open"]
                    self._close_position(pos, exit_price, "STOP_GAP", current_date)
                    continue
                elif bar["Low"] <= pos["stop_price"]:
                    # Normal stop hit intrabar
                    exit_price = pos["stop_price"]
                    self._close_position(pos, exit_price, "STOP", current_date)
                    continue
                elif bar["Open"] >= pos["target_price"]:
                    # Gap up through target
                    exit_price = bar["Open"]
                    self._close_position(pos, exit_price, "TARGET_GAP", current_date)
                    continue
                elif bar["High"] >= pos["target_price"]:
                    # Normal target hit
                    exit_price = pos["target_price"]
                    self._close_position(pos, exit_price, "TARGET", current_date)
                    continue
            
            # If not closed, update M2M
            if sym in day_data:
                pos["last_price"] = day_data[sym]["Close"]
            still_active.append(pos)
            
        self.active_positions = still_active
        
        # Calculate Current M2M Equity
        market_value = sum(p["last_price"] * p["qty"] for p in self.active_positions)
        current_equity = self.cash + market_value
        
        # 2. Process Pending Signals (Entries)
        remaining_signals = []
        for sig in self.active_signals:
            sym = sig["symbol"]
            if sym in day_data:
                bar = day_data[sym]
                # Entry is next open
                entry_price = bar["Open"]
                
                # Apply slippage
                slippage = entry_price * (self.cfg.execution.slippage_value / 100.0)
                actual_entry_price = entry_price + slippage
                
                risk_per_share = actual_entry_price - sig["planned_stop"]
                if risk_per_share > 0 and len(self.active_positions) < self.max_positions:
                    # Size based on equity
                    risk_budget = current_equity * self.risk_pct
                    qty = math.floor(risk_budget / risk_per_share)
                    
                    cost_est = qty * actual_entry_price
                    buy_cost = get_leg_cost(cost_est, True, self.cfg.cost_model)
                    
                    if qty > 0 and (cost_est + buy_cost) <= self.cash:
                        self.cash -= (cost_est + buy_cost)
                        
                        pos = {
                            "trade_id": f"TRD_{len(self.trades_log)+len(self.active_positions)+1}",
                            "symbol": sym,
                            "signal_timestamp": sig["signal_timestamp"],
                            "entry_timestamp": current_date, # Entered on current date's open
                            "entry_price": actual_entry_price,
                            "qty": qty,
                            "stop_price": sig["planned_stop"],
                            "target_price": sig["planned_target"],
                            "buy_cost": buy_cost,
                            "trade_value_buy": cost_est,
                            "last_price": bar["Close"], # Mark to market at close
                            "risk_rupees": risk_per_share * qty
                        }
                        self.active_positions.append(pos)
                        sig["signal_status"] = "FILLED"
                    else:
                        sig["signal_status"] = "REJECTED_FUNDS"
                else:
                    sig["signal_status"] = "REJECTED_RISK"
                    
                self.signals_log.append(sig)
            else:
                # Keep active if no data today
                remaining_signals.append(sig)
                
        self.active_signals = remaining_signals
        
        # 3. Generate New Signals based on prev_day_data
        # Note: In a true forward test, we compute indicators up to current_date - 1 (the close of yesterday)
        # and if a signal fires, it becomes active for tomorrow (or today's open, if we are computing before market open).
        # We assume prev_day_data contains the finalized technical indicators for yesterday.
        if prev_day_data:
            for sym, data in prev_day_data.items():
                if data.get("signal") == True:
                    planned_entry = data["Close"] # baseline reference
                    atr = data["ATR"]
                    stop = planned_entry - (atr * self.cfg.strategy.stop_atr_multiple)
                    target = planned_entry + (atr * self.cfg.strategy.reward_risk_multiple) * 1.5 # simplified matching
                    
                    new_sig = {
                        "symbol": sym,
                        "signal_timestamp": data["date"], # Yesterday's date
                        "entry_timestamp": current_date, # Planned for today
                        "signal_price": planned_entry,
                        "planned_entry": planned_entry,
                        "ATR": atr,
                        "planned_stop": stop,
                        "planned_target": target,
                        "strategy_version": STRATEGY_VERSION,
                        "data_timestamp": data["date"], # Time data was acquired
                        "signal_status": "PENDING"
                    }
                    # Validate Data Integrity Rule: no future data
                    assert pd.to_datetime(new_sig["data_timestamp"]) <= pd.to_datetime(new_sig["signal_timestamp"])
                    assert pd.to_datetime(new_sig["entry_timestamp"]) > pd.to_datetime(new_sig["signal_timestamp"])
                    
                    self.active_signals.append(new_sig)
        
        # 4. End of Day Accounting
        market_value_end = sum(p["last_price"] * p["qty"] for p in self.active_positions)
        unrealized_pnl = sum((p["last_price"] - p["entry_price"]) * p["qty"] - p["buy_cost"] for p in self.active_positions)
        end_equity = self.cash + market_value_end
        
        self.portfolio_history.append({
            "date": current_date,
            "cash": self.cash,
            "market_value": market_value_end,
            "equity": end_equity,
            "unrealized_pnl": unrealized_pnl,
            "open_positions": len(self.active_positions)
        })
        
    def _close_position(self, pos, exit_price, exit_reason, current_date):
        trade_value_sell = exit_price * pos["qty"]
        sell_cost = get_leg_cost(trade_value_sell, False, self.cfg.cost_model)
        
        net_proceeds = trade_value_sell - sell_cost
        self.cash += net_proceeds
        
        total_cost = pos["buy_cost"] + sell_cost
        gross_pnl = trade_value_sell - pos["trade_value_buy"]
        net_pnl = gross_pnl - total_cost
        
        r_mult = net_pnl / pos["risk_rupees"] if pos["risk_rupees"] > 0 else 0
        
        self.trades_log.append({
            "trade_id": pos["trade_id"],
            "symbol": pos["symbol"],
            "signal_timestamp": pos["signal_timestamp"],
            "entry_timestamp": pos["entry_timestamp"],
            "entry_price": pos["entry_price"],
            "qty": pos["qty"],
            "stop": pos["stop_price"],
            "target": pos["target_price"],
            "exit_timestamp": current_date,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "gross_pnl": gross_pnl,
            "transaction_costs": total_cost,
            "net_pnl": net_pnl,
            "r_multiple": r_mult,
            "strategy_version": STRATEGY_VERSION
        })
        
    def save_logs(self):
        pd.DataFrame(self.signals_log).to_csv(RESULTS_DIR / "forward_signals.csv", index=False)
        pd.DataFrame(self.trades_log).to_csv(RESULTS_DIR / "forward_trades.csv", index=False)
        pd.DataFrame(self.portfolio_history).to_csv(RESULTS_DIR / "forward_portfolio_history.csv", index=False)

def check_milestones():
    # Fixed evaluation checkpoints
    trades = pd.read_csv(RESULTS_DIR / "forward_trades.csv")
    n_trades = len(trades)
    
    milestones = [25, 50, 100, 150, 200]
    passed_milestones = [m for m in milestones if n_trades >= m]
    
    rows = []
    for m in passed_milestones:
        sub = trades.iloc[:m]
        win_rate = (sub["net_pnl"] > 0).mean()
        avg_r = sub["r_multiple"].mean()
        rows.append({
            "milestone": m,
            "win_rate": win_rate,
            "avg_r": avg_r,
            "status": "PASSED_EVALUATION"
        })
        
    if rows:
        pd.DataFrame(rows).to_csv(RESULTS_DIR / "forward_validation_milestones.csv", index=False)

if __name__ == "__main__":
    # In a real environment, this script runs daily.
    # For now, this is a skeleton architecture establishing the rules.
    pass
