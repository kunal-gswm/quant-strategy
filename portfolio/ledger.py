import pandas as pd

class TradeLedger:
    def __init__(self):
        self.trades = []
        self._trade_id_counter = 1

    def record_trade(self, symbol: str, signal_timestamp, entry_timestamp, exit_timestamp,
                     entry_price: float, exit_price: float, stop_price: float, target_price: float,
                     atr_at_signal: float, quantity: int, total_costs: float,
                     exit_reason: str, ambiguous_exit: bool):
        
        risk_per_share = entry_price - stop_price
        gross_pnl = (exit_price - entry_price) * quantity
        net_pnl = gross_pnl - total_costs
        
        r_multiple = net_pnl / (risk_per_share * quantity) if risk_per_share > 0 and quantity > 0 else float("nan")
        
        self.trades.append({
            "trade_id": self._trade_id_counter,
            "symbol": symbol,
            "signal_timestamp": signal_timestamp,
            "entry_timestamp": entry_timestamp,
            "exit_timestamp": exit_timestamp,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_price": stop_price,
            "target_price": target_price,
            "atr_at_signal": atr_at_signal,
            "risk_per_share": risk_per_share,
            "quantity": quantity,
            "gross_pnl": gross_pnl,
            "total_costs": total_costs,
            "net_pnl": net_pnl,
            "r_multiple": r_multiple,
            "exit_reason": exit_reason,
            "ambiguous_exit": ambiguous_exit
        })
        self._trade_id_counter += 1

    def to_dataframe(self):
        return pd.DataFrame(self.trades)
