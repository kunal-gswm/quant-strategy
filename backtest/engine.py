import pandas as pd
from execution.slippage import apply_slippage
from execution.cost_model import compute_trade_costs
from backtest.execution import check_exit, OpenPosition, ExitReason
from backtest.position import size_position
from portfolio.ledger import TradeLedger

class BacktestEngine:
    def __init__(self, strategy, config):
        self.strategy = strategy
        self.config = config
        self.ledger = TradeLedger()

    def run(self, df: pd.DataFrame, symbol: str = "UNKNOWN"):
        
        signals = self.strategy.generate_signals(df)
        
        available_cash = self.config.starting_capital
        open_position = None
        pending_order = None
        
        equity_curve = []

        for i in range(len(df)):
            t = df.index[i]
            row = df.iloc[i]
            
            bar_open = row["open"]
            bar_high = row["high"]
            bar_low = row["low"]
            bar_close = row["close"]
            
            if open_position is not None:
                reason, exit_level, is_ambiguous = check_exit(
                    open_position, bar_high, bar_low, self.config.execution.intrabar_policy
                )
                
                if reason is not None:
                    exit_fill = apply_slippage(
                        exit_level, "sell", 
                        self.config.execution.slippage_type, 
                        self.config.execution.slippage_value
                    )
                    
                    trade_value_buy = open_position.entry_price * open_position.quantity
                    trade_value_sell = exit_fill * open_position.quantity
                    costs = compute_trade_costs(trade_value_buy, trade_value_sell, self.config.cost_model)
                    
                    self.ledger.record_trade(
                        symbol=symbol,
                        signal_timestamp=open_position.signal_timestamp,
                        entry_timestamp=open_position.entry_timestamp,
                        exit_timestamp=t,
                        entry_price=open_position.entry_price,
                        exit_price=exit_fill,
                        stop_price=open_position.stop_price,
                        target_price=open_position.target_price,
                        atr_at_signal=open_position.atr_at_signal,
                        quantity=open_position.quantity,
                        total_costs=costs,
                        exit_reason=reason.value,
                        ambiguous_exit=is_ambiguous
                    )
                    
                    net_pnl = (exit_fill - open_position.entry_price) * open_position.quantity - costs
                    available_cash += (open_position.entry_price * open_position.quantity + net_pnl)
                    open_position = None

            if open_position is None and pending_order is None:
                if signals.iloc[i]:
                    atr = df["atr14"].iloc[i]
                    pending_order = (t, atr)
                    
            if pending_order is not None and open_position is None and pending_order[0] != t:
                signal_ts, atr = pending_order
                
                entry_fill = apply_slippage(
                    bar_open, "buy", 
                    self.config.execution.slippage_type, 
                    self.config.execution.slippage_value
                )
                
                stop = entry_fill - self.config.strategy.stop_atr_multiple * atr
                reward_risk = self.config.strategy.reward_risk_multiple
                target = entry_fill + reward_risk * (entry_fill - stop)
                
                qty = size_position(
                    entry_fill, stop, 
                    self.config.risk.max_risk_per_trade_rupees, 
                    available_cash
                )
                
                if qty > 0:
                    open_position = OpenPosition(
                        entry_price=entry_fill,
                        stop_price=stop,
                        target_price=target,
                        quantity=qty,
                        entry_timestamp=t,
                        signal_timestamp=signal_ts,
                        atr_at_signal=atr
                    )
                    available_cash -= (entry_fill * qty)
                else:
                    pass
                
                pending_order = None

            position_value = (open_position.quantity * bar_close) if open_position else 0.0
            equity = available_cash + position_value
            equity_curve.append({
                "timestamp": t,
                "equity": equity,
                "available_cash": available_cash
            })

        if open_position is not None:
            exit_fill = bar_close 
            trade_value_buy = open_position.entry_price * open_position.quantity
            trade_value_sell = exit_fill * open_position.quantity
            costs = compute_trade_costs(trade_value_buy, trade_value_sell, self.config.cost_model)
            
            self.ledger.record_trade(
                symbol=symbol,
                signal_timestamp=open_position.signal_timestamp,
                entry_timestamp=open_position.entry_timestamp,
                exit_timestamp=df.index[-1],
                entry_price=open_position.entry_price,
                exit_price=exit_fill,
                stop_price=open_position.stop_price,
                target_price=open_position.target_price,
                atr_at_signal=open_position.atr_at_signal,
                quantity=open_position.quantity,
                total_costs=costs,
                exit_reason=ExitReason.END_OF_DATA.value,
                ambiguous_exit=False
            )
            net_pnl = (exit_fill - open_position.entry_price) * open_position.quantity - costs
            available_cash += (open_position.entry_price * open_position.quantity + net_pnl)
            open_position = None
            equity_curve[-1]["equity"] = available_cash

        return self.ledger.to_dataframe(), pd.DataFrame(equity_curve).set_index("timestamp")
