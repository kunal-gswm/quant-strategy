import os
import json
import pandas as pd
from datetime import datetime
from forward.journal_generator import generate_daily_journal, JOURNAL_DIR
from forward.engine import RESULTS_DIR

def test_journal_generation(monkeypatch, tmp_path):
    monkeypatch.setattr("forward.journal_generator.RESULTS_DIR", tmp_path)
    monkeypatch.setattr("forward.journal_generator.JOURNAL_DIR", tmp_path / "journal")
    
    # 1. No signal day
    dt = datetime(2026, 10, 1)
    generate_daily_journal(dt)
    
    jpath = tmp_path / "journal" / "2026-10-01.md"
    assert jpath.exists()
    content = jpath.read_text(encoding="utf-8")
    assert "No new TPQSE_v1.0 signals were generated" in content
    assert "No new trades were opened" in content
    
    # 2. Failed session
    generate_daily_journal(dt, session_result="BLOCKED")
    content = jpath.read_text(encoding="utf-8")
    assert "BLOCKED" in content
    
    # 3. Idempotent execution
    generate_daily_journal(dt)
    assert jpath.exists()
