import pandas as pd
from pathlib import Path

def main():
    import sys
    sys.path.append("d:/stratergy")
    from universe import get_universe
    
    RESULTS_DIR = Path("d:/stratergy/results")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    current_universe = get_universe()
    num_current = len(current_universe)
    
    trades = pd.read_csv("d:/stratergy/expanded_trades.csv")
    trades["entry_timestamp"] = pd.to_datetime(trades["entry_timestamp"])
    trades["year"] = trades["entry_timestamp"].dt.year
    
    years = [2020, 2021, 2022, 2023, 2024, 2025]
    
    rows = []
    for y in years:
        num_trades = len(trades[trades["year"] == y])
        rows.append({
            "year": y,
            "number_of_stocks_current_universe": num_current,
            "number_of_stocks_point_in_time": "N/A",
            "stocks_entering": "N/A",
            "stocks_leaving": "N/A",
            "delisted_merged_identified": 0,
            "trades_current_universe": num_trades,
            "trades_point_in_time": "N/A"
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "historical_universe_comparison.csv", index=False)
    
    print("SURVIVORSHIP STATUS: UNRESOLVED")
    print("POINT-IN-TIME DATA QUALITY: INADEQUATE")
    print("STRATEGY PARAMETERS MODIFIED: NO")
    print("ACCOUNTING LOGIC MODIFIED: NO")

if __name__ == "__main__":
    main()
