import pandas as pd
import json
import sys
from pathlib import Path
from forward.config import get_frozen_forward_config, get_configuration_fingerprint, STRATEGY_VERSION
from forward.engine import RESULTS_DIR

def validate():
    # 1. Configuration fingerprint unchanged
    fp = get_configuration_fingerprint()
    if fp["sha256"] != "1fa5372a8a97e3dea6445543c844c048d2d7257c009b595681b2f0f5fd0b5327":
        print("ERROR: Configuration fingerprint changed!")
        return False
        
    if STRATEGY_VERSION != "TPQSE_v1.0":
        print("ERROR: Strategy version changed!")
        return False

    # 2. No duplicate signal IDs
    sig_path = RESULTS_DIR / "forward_signals.csv"
    if sig_path.exists():
        sigs = pd.read_csv(sig_path)
        sig_id_col = "signal_id" if "signal_id" in sigs.columns else "trade_id"
        if sigs.duplicated(subset=[sig_id_col]).any():
            print("ERROR: Duplicate signal IDs found in forward_signals.csv")
            return False
            
    # 3. No duplicate trade IDs
    tr_path = RESULTS_DIR / "forward_trades.csv"
    if tr_path.exists():
        trades = pd.read_csv(tr_path)
        if trades.duplicated(subset=["trade_id"]).any():
            print("ERROR: Duplicate trade IDs found in forward_trades.csv")
            return False

    # 4. State files parse correctly
    pos_path = RESULTS_DIR / "forward_open_positions.json"
    if pos_path.exists():
        try:
            with open(pos_path, "r") as f:
                json.load(f)
        except Exception as e:
            print(f"ERROR: forward_open_positions.json is malformed: {e}")
            return False

    print("Output validation passed.")
    return True

if __name__ == "__main__":
    if not validate():
        sys.exit(1)
    sys.exit(0)
