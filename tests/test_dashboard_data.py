import pytest
import pandas as pd
import json
from pathlib import Path
from dashboard.data_loader import DataLoader

@pytest.fixture
def data_loader(tmp_path):
    f_dir = tmp_path / "forward"
    h_dir = tmp_path / "historical"
    f_dir.mkdir()
    h_dir.mkdir()
    return DataLoader(str(f_dir), str(h_dir)), f_dir, h_dir

def test_data_loader_missing_file(data_loader):
    dl, _, _ = data_loader
    df = dl.get_forward_signals()
    assert df.empty

def test_data_loader_malformed_csv(data_loader):
    dl, f_dir, _ = data_loader
    bad_csv = f_dir / "forward_signals.csv"
    bad_csv.write_text("this,is,not,a,valid,csv\n1,2,3")
    df = dl.get_forward_signals()
    assert df.empty

def test_data_loader_empty_dataset(data_loader):
    dl, f_dir, _ = data_loader
    empty_csv = f_dir / "forward_signals.csv"
    empty_csv.write_text("signal_id,symbol\n")
    df = dl.get_forward_signals()
    assert df.empty

def test_data_loader_missing_columns(data_loader):
    dl, f_dir, _ = data_loader
    csv = f_dir / "forward_signals.csv"
    # Missing required column 'signal_id'
    csv.write_text("symbol,signal_timestamp\nAAPL,2026-09-29\n")
    df = dl.get_forward_signals()
    assert df.empty

def test_data_loader_corrupted_json(data_loader):
    dl, f_dir, _ = data_loader
    bad_json = f_dir / "forward_open_positions.json"
    bad_json.write_text("{this is not json")
    df = dl.get_forward_positions()
    assert df.empty

def test_data_loader_valid_json(data_loader):
    dl, f_dir, _ = data_loader
    good_json = f_dir / "forward_open_positions.json"
    good_json.write_text('[{"trade_id": "1", "symbol": "AAPL"}]')
    df = dl.get_forward_positions()
    assert not df.empty
    assert len(df) == 1
    assert df.iloc[0]["symbol"] == "AAPL"
