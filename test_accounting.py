import pytest
import pandas as pd
from config import BacktestConfig
from portfolio_engine import simulate_portfolio, get_leg_cost

class DummyConfig:
    brokerage_type = "percentage"
    brokerage_value = 0.0
    exchange_transaction_charge_pct = 0.0
    stt_pct_delivery = 0.0
    sebi_charges_per_crore = 0.0
    stamp_duty_pct_buy_leg = 0.0
    gst_pct = 0.0

@pytest.fixture
def base_cfg():
    return DummyConfig()

def create_prepared_data(prices, dates):
    df = pd.DataFrame({"Close": prices}, index=pd.to_datetime(dates))
    return {"DUMMY": df}

def create_trades_df(entry_ts, exit_ts, entry_price, exit_price, stop_price=95):
    trade = {
        "symbol": "DUMMY",
        "signal_timestamp": entry_ts,
        "entry_timestamp": entry_ts,
        "exit_timestamp": exit_ts,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price": stop_price,
        "r_multiple": 1.0
    }
    return pd.DataFrame([trade])

def test_opening_and_unrealized_profit(base_cfg):
    dates = ["2020-01-01", "2020-01-02", "2020-01-03"]
    prices = [100.0, 105.0, 105.0]
    prep = create_prepared_data(prices, dates)
    
    trades = create_trades_df("2020-01-01", "2020-01-03", 100.0, 105.0, 95.0)
    
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.01)
    
    # Day 1: Entry
    # Risk budget = 100000 * 0.01 = 1000. Risk per share = 100 - 95 = 5. Qty = 200.
    # Cost = 0. Trade value = 20000. Cash = 80000. Equity = 100000.
    day1 = hist.iloc[0]
    assert day1["cash"] == 80000
    assert day1["equity"] == 100000
    assert day1["open_positions"] == 1
    
    # Day 2: Unrealized profit
    # Price rises to 105. Position value = 21000. Cash = 80000. Equity = 101000.
    day2 = hist.iloc[1]
    assert day2["cash"] == 80000
    assert day2["equity"] == 101000
    assert day2["unrealized_pnl"] == 1000
    
    # Day 3: Closing
    # Position closes at 105. Proceeds = 21000. Cash = 101000. Equity = 101000.
    day3 = hist.iloc[2]
    assert day3["cash"] == 101000
    assert day3["equity"] == 101000
    assert day3["open_positions"] == 0

def test_unrealized_loss(base_cfg):
    dates = ["2020-01-01", "2020-01-02", "2020-01-03"]
    prices = [100.0, 95.0, 95.0]
    prep = create_prepared_data(prices, dates)
    trades = create_trades_df("2020-01-01", "2020-01-03", 100.0, 95.0, 95.0)
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.01)
    
    day2 = hist.iloc[1]
    assert day2["equity"] == 99000
    assert day2["unrealized_pnl"] == -1000

def test_integer_quantity_rounding_and_risk_sizing(base_cfg):
    dates = ["2020-01-01", "2020-01-02"]
    prices = [100.0, 100.0]
    prep = create_prepared_data(prices, dates)
    
    # Risk budget = 100,000 * 0.005 = 500
    # per share risk = 3. Qty = 500 / 3 = 166.66 -> 166.
    trades = create_trades_df("2020-01-01", "2020-01-02", 100.0, 100.0, 97.0)
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.005)
    
    qty = exec_trades.iloc[0]["qty"]
    assert qty == 166
    
    # For 1% risk: budget = 1000. Qty = 1000 / 3 = 333.33 -> 333
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.01)
    qty2 = exec_trades.iloc[0]["qty"]
    assert qty2 == 333

def test_insufficient_cash(base_cfg):
    dates = ["2020-01-01", "2020-01-02"]
    prices = [100.0, 100.0]
    prep = create_prepared_data(prices, dates)
    
    # Risk budget = 100,000 * 0.05 = 5000. Risk per share = 1. Qty = 5000.
    # Total cost = 500,000 > 100,000.
    # Should cap at 1000 qty.
    trades = create_trades_df("2020-01-01", "2020-01-02", 100.0, 100.0, 99.0)
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.05)
    
    qty = exec_trades.iloc[0]["qty"]
    assert qty == 1000

def create_prepared_data_2(prices, dates):
    df = pd.DataFrame({"Close": prices}, index=pd.to_datetime(dates))
    return {"DUMMY": df, "DUMMY2": df}

def test_multiple_simultaneous_positions(base_cfg):
    dates = ["2020-01-01", "2020-01-02", "2020-01-03"]
    prices = [100.0, 100.0, 100.0]
    prep = create_prepared_data_2(prices, dates)
    trade1 = {
        "symbol": "DUMMY",
        "signal_timestamp": "2020-01-01",
        "entry_timestamp": "2020-01-01",
        "exit_timestamp": "2020-01-03",
        "entry_price": 100.0,
        "exit_price": 100.0,
        "stop_price": 95.0,
        "r_multiple": 1.0
    }
    trade2 = {
        "symbol": "DUMMY2",
        "signal_timestamp": "2020-01-01",
        "entry_timestamp": "2020-01-01",
        "exit_timestamp": "2020-01-03",
        "entry_price": 100.0,
        "exit_price": 100.0,
        "stop_price": 95.0,
        "r_multiple": 1.0
    }
    trades = pd.DataFrame([trade1, trade2])
    
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, base_cfg, initial_capital=100000, risk_pct=0.01)
    
    day1 = hist.iloc[0]
    assert day1["open_positions"] == 2
    # Eq = 100000. Qty = 200 each. Total cash deployed = 40000.
    assert day1["cash"] == 60000
    assert day1["equity"] == 100000
def test_transaction_costs():
    cfg = DummyConfig()
    cfg.brokerage_value = 0.1 # 0.1%
    
    dates = ["2020-01-01", "2020-01-02"]
    prices = [100.0, 100.0]
    prep = create_prepared_data(prices, dates)
    trades = create_trades_df("2020-01-01", "2020-01-02", 100.0, 100.0, 95.0)
    
    end_equity, exec_trades, hist = simulate_portfolio(trades, prep, cfg, initial_capital=100000, risk_pct=0.01)
    
    # Qty = 200. Value = 20000. Cost = 0.1% = 20 per leg.
    day1 = hist.iloc[0]
    assert day1["cash"] == 100000 - 20000 - 20
    assert day1["equity"] == 100000 - 20
    
    day2 = hist.iloc[1]
    assert day2["cash"] == 100000 - 40 # 20 for buy, 20 for sell
    assert day2["equity"] == 100000 - 40
