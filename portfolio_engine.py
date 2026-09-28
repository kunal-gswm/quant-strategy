import pandas as pd
import numpy as np
import math

def get_leg_cost(value: float, is_buy_leg: bool, cfg) -> float:
    brokerage = value * (cfg.brokerage_value / 100.0) if getattr(cfg, 'brokerage_type', 'percentage') == "percentage" else getattr(cfg, 'brokerage_value', 0)
    exch = value * getattr(cfg, 'exchange_transaction_charge_pct', 0) / 100.0
    stt = value * getattr(cfg, 'stt_pct_delivery', 0) / 100.0
    sebi = value * getattr(cfg, 'sebi_charges_per_crore', 0) / 1e7
    stamp = value * getattr(cfg, 'stamp_duty_pct_buy_leg', 0) / 100.0 if is_buy_leg else 0.0
    gst_base = brokerage + exch + sebi
    gst = gst_base * getattr(cfg, 'gst_pct', 0) / 100.0
    return brokerage + exch + stt + sebi + stamp + gst

def compute_trade_costs(trade_value_buy: float, trade_value_sell: float, cfg) -> float:
    return get_leg_cost(trade_value_buy, True, cfg) + get_leg_cost(trade_value_sell, False, cfg)

def simulate_portfolio(trades, prepared_data, cfg, initial_capital=1_000_000, risk_pct=0.005, max_positions=10, max_sector_pct=0.3, cost_multiplier=1.0):
    df_trades = trades.copy()
    df_trades["signal_timestamp"] = pd.to_datetime(df_trades["signal_timestamp"])
    df_trades["entry_timestamp"] = pd.to_datetime(df_trades["entry_timestamp"])
    df_trades["exit_timestamp"] = pd.to_datetime(df_trades["exit_timestamp"])
    
    # Sort signals by timestamp
    df_trades = df_trades.sort_values(["signal_timestamp", "symbol"])
    
    if df_trades.empty:
        return initial_capital, pd.DataFrame(), pd.DataFrame()
        
    start_date = df_trades["signal_timestamp"].min()
    end_date = df_trades["exit_timestamp"].max()
    
    # Some assets might have dates that are not in all_days (weekends etc), 
    # but we just iterate over all business days or calendar days.
    # We will use the union of all indices in prepared_data between start_date and end_date.
    all_dates = set()
    for sym, df in prepared_data.items():
        sub = df.loc[start_date:end_date]
        all_dates.update(sub.index.tolist())
    # Also add signal, entry, and exit timestamps to ensure we process them
    all_dates.update(df_trades["signal_timestamp"].tolist())
    all_dates.update(df_trades["entry_timestamp"].tolist())
    all_dates.update(df_trades["exit_timestamp"].tolist())
    
    all_dates = sorted(list(all_dates))
    
    cash = float(initial_capital)
    active_positions = []
    portfolio_history = []
    executed_trades = []
    
    trade_idx = 0
    total_trades = len(df_trades)
    
    for current_date in all_dates:
        # 1. Close positions that exit on this date
        still_active = []
        for pos in active_positions:
            if pos["exit_timestamp"] == current_date:
                qty = pos["qty"]
                exit_price = pos["trade_record"]["exit_price"]
                
                trade_value_sell = exit_price * qty
                sell_cost = get_leg_cost(trade_value_sell, False, cfg) * cost_multiplier
                
                net_proceeds = trade_value_sell - sell_cost
                cash += net_proceeds
                
                total_cost = pos["buy_cost"] + sell_cost
                net_pnl = (trade_value_sell - pos["trade_value_buy"]) - total_cost
                
                r_mult = net_pnl / pos["risk_rupees"] if pos["risk_rupees"] > 0 else 0
                
                executed_trades.append({
                    "symbol": pos["symbol"],
                    "entry_timestamp": pos["entry_timestamp"],
                    "exit_timestamp": pos["exit_timestamp"],
                    "qty": qty,
                    "net_pnl": net_pnl,
                    "r_multiple": r_mult
                })
            else:
                still_active.append(pos)
        active_positions = still_active
        
        # Calculate Current M2M Equity to use for Position Sizing today
        market_value = 0
        for pos in active_positions:
            sym = pos["symbol"]
            df = prepared_data.get(sym)
            if df is not None and current_date in df.index:
                curr_price = df.loc[current_date, "Close"]
                pos["last_price"] = curr_price
            else:
                curr_price = pos["last_price"]
            
            market_value += curr_price * pos["qty"]
            
        current_equity = cash + market_value
        
        # 2. Process Entry for trades whose entry_timestamp == current_date
        # Wait, the original engine processed signals on signal_timestamp and opened them. 
        # But wait, original engine sets "entry_timestamp" which is already the exact execution time.
        # So we should process signals exactly on their signal_timestamp to reserve/calculate sizing!
        # And open them on entry_timestamp? 
        # Actually, if we process on signal_timestamp, we size based on equity at signal_timestamp.
        
        while trade_idx < total_trades and df_trades.iloc[trade_idx]["signal_timestamp"] <= current_date:
            trade = df_trades.iloc[trade_idx]
            if trade["signal_timestamp"] == current_date:
                if len(active_positions) < max_positions:
                    sector = trade.get("sector", "Unknown")
                    sector_count = sum(1 for p in active_positions if p.get("sector", "Unknown") == sector)
                    if sector_count < (max_positions * max_sector_pct):
                        stock_count = sum(1 for p in active_positions if p["symbol"] == trade["symbol"])
                        if stock_count == 0:
                            risk_per_share = trade["entry_price"] - trade["stop_price"]
                            if risk_per_share > 0:
                                # USE PORTFOLIO EQUITY FOR RISK SIZING
                                risk_budget = current_equity * risk_pct
                                qty_by_risk = math.floor(risk_budget / risk_per_share)
                                
                                # Check cash affordability
                                # We need to afford: qty * entry_price + buy_costs
                                # Approximating buy cost for affordability check
                                affordable_qty = qty_by_risk
                                while affordable_qty > 0:
                                    cost_est = affordable_qty * trade["entry_price"]
                                    if cost_est + get_leg_cost(cost_est, True, cfg) * cost_multiplier <= cash:
                                        break
                                    affordable_qty -= 1
                                
                                qty = affordable_qty
                                
                                if qty > 0:
                                    trade_value_buy = qty * trade["entry_price"]
                                    buy_cost = get_leg_cost(trade_value_buy, True, cfg) * cost_multiplier
                                    
                                    # Deduct cash immediately to open the position
                                    cash -= (trade_value_buy + buy_cost)
                                    
                                    active_positions.append({
                                        "symbol": trade["symbol"],
                                        "sector": sector,
                                        "entry_timestamp": trade["entry_timestamp"],
                                        "exit_timestamp": trade["exit_timestamp"],
                                        "entry_price": trade["entry_price"],
                                        "qty": qty,
                                        "buy_cost": buy_cost,
                                        "trade_value_buy": trade_value_buy,
                                        "risk_rupees": risk_per_share * qty,
                                        "trade_record": trade,
                                        "last_price": trade["entry_price"]
                                    })
            trade_idx += 1
            
        # Recalculate M2M Equity after any buys
        market_value_end = 0
        unrealized_pnl = 0
        for pos in active_positions:
            market_value_end += pos["last_price"] * pos["qty"]
            # To be very precise, unrealized PnL is market_value - trade_value_buy - buy_costs
            unrealized_pnl += (pos["last_price"] * pos["qty"] - pos["trade_value_buy"] - pos["buy_cost"])
            
        end_equity = cash + market_value_end
        
        portfolio_history.append({
            "date": current_date,
            "cash": cash,
            "market_value": market_value_end,
            "equity": end_equity,
            "unrealized_pnl": unrealized_pnl,
            "open_positions": len(active_positions)
        })
        
    return end_equity, pd.DataFrame(executed_trades), pd.DataFrame(portfolio_history)

def calculate_portfolio_metrics(initial_capital, final_capital, history_df, trades_df):
    if trades_df.empty:
        return {"cagr": 0, "max_dd": 0, "sharpe": 0, "profit_factor": 0, "net_return": 0, "trades": 0}
        
    net_return = (final_capital - initial_capital) / initial_capital
    days = (history_df["date"].max() - history_df["date"].min()).days
    years = days / 365.25 if days > 0 else 1
    cagr = (final_capital / initial_capital) ** (1 / years) - 1 if final_capital > 0 else 0
    
    history_df["peak"] = history_df["equity"].cummax()
    history_df["drawdown"] = (history_df["peak"] - history_df["equity"]) / history_df["peak"]
    max_dd = history_df["drawdown"].max()
    
    gross_profit = trades_df.loc[trades_df["net_pnl"] > 0, "net_pnl"].sum()
    gross_loss = abs(trades_df.loc[trades_df["net_pnl"] <= 0, "net_pnl"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Calculate daily returns properly on the calendar-day continuous series
    daily_returns = history_df.set_index("date")["equity"].resample("D").last().ffill().pct_change().dropna()
    sharpe = np.sqrt(252) * (daily_returns.mean() / daily_returns.std()) if daily_returns.std() != 0 else 0
    
    return {
        "cagr": cagr, 
        "max_dd": max_dd, 
        "sharpe": sharpe, 
        "profit_factor": profit_factor,
        "net_return": net_return, 
        "trades": len(trades_df)
    }
