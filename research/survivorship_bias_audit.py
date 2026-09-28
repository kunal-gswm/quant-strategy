import pandas as pd

def main():
    rows = [
        {"metric": "Historical constituents available", "value": "NO", "notes": "No point-in-time NSE membership data"},
        {"metric": "Delisted/Suspended stocks included", "value": "NO", "notes": "Only currently active stocks are listed in universe.py"},
        {"metric": "Current Active Stocks in Universe", "value": "180", "notes": "From universe.py (approximate, actual available varies by cache)"},
        {"metric": "Historical ticker changes handled", "value": "NO", "notes": "Yahoo Finance data does not robustly map old tickers"},
        {"metric": "Most affected years", "value": "2018-2020", "notes": "The further back in time, the higher the distortion due to companies that delisted before 2025"}
    ]
    pd.DataFrame(rows).to_csv("d:/stratergy/results/survivorship_bias_audit.csv", index=False)

if __name__ == "__main__":
    main()
