import streamlit as st
import pandas as pd

def render_todays_signals(dl):
    st.header("Today's Signals")
    signals = dl.get_forward_signals()
    if signals.empty:
        st.info("No signals found in the ledger.")
        return
        
    # Filter for VALID and today's date if possible. We just show all active or recent.
    # The prompt: "Only show signals generated from the current forward session."
    # We can filter by max date in the signals log.
    latest_date = signals["signal_timestamp"].max()
    today_signals = signals[signals["signal_timestamp"] == latest_date]
    
    if today_signals.empty:
        st.info("No signals for the latest session.")
        return
        
    st.dataframe(today_signals[["symbol", "direction", "planned_entry", "stop_loss", "target", "risk_reward_ratio", "position_size", "capital_at_risk", "signal_status", "signal_reason"]], use_container_width=True)

def render_open_positions(dl):
    st.header("Open Positions")
    positions = dl.get_forward_positions()
    if positions.empty:
        st.info("No open positions currently.")
        return
        
    # Need: Symbol, Entry, Current Price, Stop, Target, Unrealized P&L, R multiple, Position Size, Entry Date
    display_cols = []
    for _, pos in positions.iterrows():
        pnl = (pos["last_price"] - pos["actual_entry"]) * pos["qty"] - pos["buy_cost"]
        rmult = pnl / pos["initial_risk_rupees"] if pos["initial_risk_rupees"] > 0 else 0
        display_cols.append({
            "Symbol": pos["symbol"],
            "Entry": pos["actual_entry"],
            "Current Price": pos["last_price"],
            "Stop": pos["stop_price"],
            "Target": pos["target_price"],
            "Unrealized P&L": round(pnl, 2),
            "R multiple": round(rmult, 2),
            "Position Size": pos["qty"],
            "Entry Date": pos["entry_timestamp"]
        })
        
    st.dataframe(pd.DataFrame(display_cols), use_container_width=True)

def render_strategy_health(dl):
    st.header("Strategy Health")
    health = dl.get_health_metrics()
    if health.empty:
        st.warning("No health metrics available.")
        return
        
    latest = health.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Strategy Version", latest.get("strategy_version", "N/A"))
    col2.metric("Forward Status", latest.get("execution_status", "N/A"))
    
    trades = dl.get_forward_trades()
    completed = len(trades)
    
    win_rate = 0
    expectancy = 0
    pf = 0
    if completed > 0:
        win_rate = (trades["net_pnl"] > 0).mean()
        expectancy = trades["r_multiple"].mean()
        gp = trades.loc[trades["net_pnl"] > 0, "net_pnl"].sum()
        gl = abs(trades.loc[trades["net_pnl"] <= 0, "net_pnl"].sum())
        pf = gp / gl if gl > 0 else float('inf')
        
    col3.metric("Completed Trades", completed)
    col4.metric("Win Rate", f"{win_rate:.2%}")
    
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expectancy (R)", f"{expectancy:.2f}")
    c2.metric("Profit Factor", f"{pf:.2f}")
    
    portfolio = dl.get_forward_portfolio()
    cur_eq = 1000000.0
    dd = 0.0
    if not portfolio.empty:
        cur_eq = portfolio.iloc[-1]["equity"]
        peak = portfolio["equity"].cummax()
        dd_series = (portfolio["equity"] - peak) / peak
        dd = dd_series.min() * 100 if len(dd_series) > 0 else 0.0
        
    c3.metric("Current Equity", f"₹{cur_eq:,.2f}")
    c4.metric("Current Drawdown", f"{dd:.2f}%")
    
    st.markdown("### Milestones")
    ms = [25, 50, 100, 150, 200]
    cols = st.columns(5)
    for i, m in enumerate(ms):
        status = "COMPLETED" if completed >= m else ("IN PROGRESS" if completed > 0 else "NOT REACHED")
        cols[i].markdown(f"**{m}-trade:** {status}")

def render_failure_conditions(dl):
    st.header("Failure Conditions")
    
    trades = dl.get_forward_trades()
    completed = len(trades)
    expectancy = trades["r_multiple"].mean() if completed > 0 else 0
    
    portfolio = dl.get_forward_portfolio()
    dd = 0.0
    if not portfolio.empty:
        peak = portfolio["equity"].cummax()
        dd_series = (portfolio["equity"] - peak) / peak
        dd = dd_series.min() * 100 if len(dd_series) > 0 else 0.0
        
    # Expectancy
    exp_status = "OK"
    if completed >= 50 and expectancy < 0:
        exp_status = "TRIGGERED"
        
    # Drawdown
    dd_status = "OK"
    if dd < -15.0:
        dd_status = "TRIGGERED"
    elif dd < -10.0:
        dd_status = "WARNING"
        
    # Slippage degradation
    slip_status = "OK"
    if completed >= 25:
        slip_window = trades.tail(25)
        # Check if they have slippage_cost to compute slip_pct
        if "actual_entry" in slip_window.columns and "planned_entry" in slip_window.columns:
            e_slip_pct = (slip_window["actual_entry"] - slip_window["planned_entry"]) / slip_window["planned_entry"] * 100
            exceeds = e_slip_pct > 0.10
            # longest consecutive
            longest = 0
            curr = 0
            for val in exceeds:
                if val:
                    curr += 1
                    longest = max(longest, curr)
                else:
                    curr = 0
            if longest >= 25:
                slip_status = "TRIGGERED"
            elif longest >= 10:
                slip_status = "WARNING"
                
    # Data Quality
    data_status = "OK"
    health = dl.get_health_metrics()
    if not health.empty:
        latest = health.iloc[-1]
        agg_fresh = latest.get("aggregate_freshness", "ALL_FRESH")
        if agg_fresh in ("DATA_DELAY", "NO_DATA"):
            data_status = "WARNING"
            
    st.table(pd.DataFrame([
        {"Condition": "Expectancy R < 0 after 50 trades", "Status": exp_status},
        {"Condition": "Drawdown > 15%", "Status": dd_status},
        {"Condition": "Slippage degradation", "Status": slip_status},
        {"Condition": "Data quality failure", "Status": data_status}
    ]))

def render_historical_research(dl):
    st.header("Historical Research (Reference Only)")
    st.warning("These are backtest out-of-sample results. Do not confuse with live forward testing.")
    
    trades = dl.get_historical_trades()
    if trades.empty:
        st.info("Historical data not found.")
        return
        
    completed = len(trades)
    win_rate = (trades["net_pnl"] > 0).mean() if completed > 0 else 0
    expectancy = trades["r_multiple"].mean() if completed > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Historical Trades", completed)
    col2.metric("Historical Win Rate", f"{win_rate:.2%}")
    col3.metric("Historical Expectancy", f"{expectancy:.2f}")

def render_system_health(dl):
    st.header("System Health")
    health = dl.get_health_metrics()
    if health.empty:
        st.warning("No system health data.")
        return
        
    latest = health.iloc[-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Last Forward Session:** {latest.get('execution_timestamp', 'N/A')}")
        st.markdown(f"**Aggregate Freshness:** {latest.get('aggregate_freshness', 'N/A')}")
        st.markdown(f"**Execution Status:** {latest.get('execution_status', 'N/A')}")
        st.markdown(f"**Integrity Status:** {latest.get('integrity_status', 'N/A')}")
    
    with col2:
        st.markdown(f"**Symbols Expected:** {latest.get('symbols_expected', 'N/A')}")
        st.markdown(f"**Symbols Failed:** {latest.get('symbols_failed', 'N/A')}")
        st.markdown(f"**Config Fingerprint:** {latest.get('config_fingerprint', 'N/A')[:16]}...")
        
    univ_health = dl.get_universe_health()
    if not univ_health.empty:
        st.subheader("Missing / Failed Symbols")
        failed = univ_health[univ_health["freshness_status"] != "FRESH"]
        if not failed.empty:
            st.dataframe(failed[["symbol", "freshness_status", "failure_classification"]])
        else:
            st.success("All symbols are fresh.")
