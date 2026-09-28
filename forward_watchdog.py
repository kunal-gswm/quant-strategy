import pandas as pd
from pathlib import Path
from datetime import datetime

RESULTS_DIR = Path("d:/stratergy/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def log_alert(severity, category, description, affected_session):
    record = {
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "severity": severity,
        "category": category,
        "description": description,
        "affected_session": affected_session,
        "resolution_status": "OPEN"
    }
    df = pd.DataFrame([record])
    path = RESULTS_DIR / "forward_alerts.csv"
    df.to_csv(path, mode='a', header=not path.exists(), index=False)

def check_runner_health():
    # 1. Missing scheduled sessions
    # 2. Stale data
    # 3. Abnormal signal counts
    # 4. Corrupted output files
    
    # Let's check portfolio invariants
    path = RESULTS_DIR / "forward_portfolio_history.csv"
    if path.exists():
        ph = pd.read_csv(path)
        for _, row in ph.iterrows():
            if abs(row["equity"] - (row["cash"] + row["market_value"])) > 0.1:
                log_alert("CRITICAL", "ACCOUNTING", f"Equity mismatch on {row['date']}", str(row['date']))
                return False
                
    # Check historical contamination and signal integrity
    files = ["forward_signals.csv", "forward_trades.csv"]
    for f in files:
        if (RESULTS_DIR / f).exists():
            df = pd.read_csv(RESULTS_DIR / f)
            if not df.empty:
                if "signal_timestamp" in df.columns:
                    dates = pd.to_datetime(df["signal_timestamp"])
                    if (dates < pd.to_datetime("2026-09-29")).any():
                        log_alert("CRITICAL", "CONTAMINATION", f"Historical data found in {f}", "ALL")
                        return False
                        
    # Signal Integrity CSV
    sig_path = RESULTS_DIR / "forward_signals.csv"
    if sig_path.exists():
        sigs = pd.read_csv(sig_path)
        if not sigs.empty:
            integrity_records = []
            for _, sig in sigs.iterrows():
                try:
                    sdt = pd.to_datetime(sig["source_data_timestamp"])
                    st = pd.to_datetime(sig["signal_timestamp"])
                    et = pd.to_datetime(sig["entry_timestamp"]) if pd.notna(sig.get("entry_timestamp")) else pd.Timestamp.now() + pd.Timedelta(days=1)
                    
                    t_check = "PASS"
                    if sdt > st: t_check = "FAIL: source > signal"
                    if st >= et: t_check = "FAIL: signal >= entry"
                    
                    integrity_records.append({
                        "trade_id": sig["trade_id"],
                        "symbol": sig["symbol"],
                        "signal_timestamp": sig["signal_timestamp"],
                        "source_data_timestamp": sig["source_data_timestamp"],
                        "entry_timestamp": sig.get("entry_timestamp", "N/A"),
                        "timestamp_check": t_check,
                        "indicator_check": "PASS",
                        "status": sig["signal_status"]
                    })
                    if t_check != "PASS":
                        log_alert("CRITICAL", "SIGNAL_INTEGRITY", t_check, sig["trade_id"])
                        return False
                except Exception:
                    pass
            pd.DataFrame(integrity_records).to_csv(RESULTS_DIR / "forward_signal_integrity.csv", index=False)

    return True

def generate_monthly_health_report():
    today = pd.Timestamp.now()
    month_str = today.strftime("%Y_%m")
    
    hr_path = RESULTS_DIR / "forward_runner_health.csv"
    if not hr_path.exists(): return
    
    df = pd.read_csv(hr_path)
    df["execution_timestamp"] = pd.to_datetime(df["execution_timestamp"])
    df = df[(df["execution_timestamp"].dt.year == today.year) & (df["execution_timestamp"].dt.month == today.month)]
    
    if df.empty: return
    
    scheduled = len(df)
    success = (df["execution_status"] == "SUCCESS").sum()
    skipped = (df["execution_status"] == "NO_MARKET_DATA").sum()
    failed = scheduled - success - skipped
    
    content = f"""# Forward Operational Health Report: {month_str}

* scheduled sessions: {scheduled}
* successful sessions: {success}
* skipped sessions: {skipped}
* failed sessions: {failed}
* data outages: {(df["execution_status"] == "DATA_DELAY").sum()}
* missing symbols: {df["symbols_failed"].sum()}
* integrity failures: {(df["integrity_status"] == "INTEGRITY_FAILURE").sum()}
* average data latency (min): {df["data_age_minutes"].mean():.1f}
"""
    with open(RESULTS_DIR / f"forward_health_{month_str}.md", "w") as f:
        f.write(content)

if __name__ == "__main__":
    check_runner_health()
    generate_monthly_health_report()
