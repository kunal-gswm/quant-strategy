import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append("d:/stratergy")
from forward.runner import fetch_and_prepare_data, run_daily
from forward.config import get_frozen_forward_config
import forward.engine

@pytest.fixture(autouse=True)
def isolated_results(isolated_results_dir):
    pass

def make_mock_data(symbols, max_date, missing_sym=None, stale_sym=None):
    # max_date is the "fresh" date
    data_dict = {}
    
    dates_fresh = pd.date_range(end=max_date, periods=10, freq='B')
    dates_stale = pd.date_range(end=max_date - pd.Timedelta(days=2), periods=10, freq='B')
    
    for sym in symbols:
        if sym == missing_sym:
            continue
        
        dates = dates_stale if sym == stale_sym else dates_fresh
        
        df = pd.DataFrame({
            "Open": [100]*len(dates),
            "High": [105]*len(dates),
            "Low": [95]*len(dates),
            "Close": [102]*len(dates),
            "Volume": [1000]*len(dates)
        }, index=dates)
        
        data_dict[sym] = df
        
    if not data_dict:
        return pd.DataFrame()
        
    return pd.concat(data_dict, axis=1)

@patch("forward.runner.yf.download")
def test_case_a_all_fresh(mock_download):
    # Case A: All symbols fresh -> ALL_FRESH
    universe = [{"symbol": f"S{i}"} for i in range(1, 11)]
    today = pd.Timestamp("2026-09-29") # Tuesday
    mock_download.return_value = make_mock_data([u["symbol"] for u in universe], today)
    
    day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, today)
    
    assert len(sym_health) == 10
    assert all(h["status"] == "FRESH" for h in sym_health.values())

@patch("forward.runner.yf.download")
def test_case_b_partial_stale(mock_download, monkeypatch):
    # Case B: 179 fresh, 1 stale -> PARTIAL_STALE
    universe = [{"symbol": f"S{i}"} for i in range(1, 11)]
    today = pd.Timestamp("2026-09-29")
    mock_download.return_value = make_mock_data([u["symbol"] for u in universe], today, stale_sym="S1")
    
    with patch("forward.runner.fetch_and_prepare_data") as mock_fetch:
        day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, today)
        mock_fetch.return_value = (day_data, prev, max_ts, exp, proc, fail, sym_health)
        
        monkeypatch.setattr("forward.runner.pd.Timestamp.now", lambda: pd.Timestamp("2026-09-29 16:30:00"))
        
        run_daily()
        
        df = pd.read_csv(forward.engine.RESULTS_DIR / "forward_runner_health.csv")
        assert df.iloc[-1]["aggregate_freshness"] == "PARTIAL_STALE"

@patch("forward.runner.yf.download")
def test_case_c_partial_missing(mock_download, monkeypatch):
    # Case C: 180 fresh, 1 no data -> PARTIAL_MISSING
    universe = [{"symbol": f"S{i}"} for i in range(1, 11)]
    today = pd.Timestamp("2026-09-29")
    mock_download.return_value = make_mock_data([u["symbol"] for u in universe], today, missing_sym="S1")
    
    with patch("forward.runner.fetch_and_prepare_data") as mock_fetch:
        day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, today)
        mock_fetch.return_value = (day_data, prev, max_ts, exp, proc, fail, sym_health)
        
        monkeypatch.setattr("forward.runner.pd.Timestamp.now", lambda: pd.Timestamp("2026-09-29 16:30:00"))
        
        run_daily()
        
        df = pd.read_csv(forward.engine.RESULTS_DIR / "forward_runner_health.csv")
        assert df.iloc[-1]["aggregate_freshness"] == "PARTIAL_MISSING"

@patch("forward.runner.yf.download")
def test_case_d_all_stale(mock_download, monkeypatch):
    # Case D: All symbols stale -> DATA_DELAY
    universe = [{"symbol": f"S{i}"} for i in range(1, 11)]
    today = pd.Timestamp("2026-09-29")
    
    # All stale by setting max_date to old date
    stale_date = pd.Timestamp("2026-09-24") # Thursday
    mock_download.return_value = make_mock_data([u["symbol"] for u in universe], stale_date)
    
    with patch("forward.runner.fetch_and_prepare_data") as mock_fetch:
        day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, today)
        mock_fetch.return_value = (day_data, prev, max_ts, exp, proc, fail, sym_health)
        
        monkeypatch.setattr("forward.runner.pd.Timestamp.now", lambda: pd.Timestamp("2026-09-29 16:30:00")) # execution on Tuesday
        
        run_daily()
        
        df = pd.read_csv(forward.engine.RESULTS_DIR / "forward_runner_health.csv")
        assert df.iloc[-1]["aggregate_freshness"] == "DATA_DELAY"
        assert df.iloc[-1]["execution_status"] == "DATA_DELAY"

@patch("forward.runner.yf.download")
def test_case_e_mapping_failure(mock_download, monkeypatch):
    # Case E: Yahoo ticker mapping failure -> DOWNLOAD_ERROR
    universe = [{"symbol": "GOOD"}, {"symbol": "BAD.NS"}]
    today = pd.Timestamp("2026-09-29")
    
    # BAD.NS is not in data columns
    mock_download.return_value = make_mock_data(["GOOD"], today)
    
    day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, today)
    
    assert sym_health["BAD.NS"]["status"] == "DOWNLOAD_ERROR"
    assert sym_health["BAD.NS"]["failure_classification"] == "YAHOO_TICKER_MAPPING_FAILURE"

@patch("forward.runner.yf.download")
def test_case_f_weekend(mock_download, monkeypatch):
    # Case F: Weekend -> ALL_FRESH if data_timestamp matches expected Friday
    universe = [{"symbol": f"S{i}"} for i in range(1, 11)]
    saturday = pd.Timestamp("2026-09-26")
    friday = pd.Timestamp("2026-09-25")
    
    mock_download.return_value = make_mock_data([u["symbol"] for u in universe], friday)
    
    with patch("forward.runner.fetch_and_prepare_data") as mock_fetch:
        day_data, prev, max_ts, exp, proc, fail, sym_health = fetch_and_prepare_data(universe, saturday)
        mock_fetch.return_value = (day_data, prev, max_ts, exp, proc, fail, sym_health)
        
        monkeypatch.setattr("forward.runner.pd.Timestamp.now", lambda: pd.Timestamp("2026-09-26 12:00:00"))
        
        run_daily()
        
        df = pd.read_csv(forward.engine.RESULTS_DIR / "forward_runner_health.csv")
        assert df.iloc[-1]["aggregate_freshness"] == "ALL_FRESH"
        assert df.iloc[-1]["execution_status"] == "NO_MARKET_DATA"
