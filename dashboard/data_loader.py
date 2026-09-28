import pandas as pd
import json
from pathlib import Path

class DataLoader:
    def __init__(self, forward_dir: str, historical_dir: str):
        self.forward_dir = Path(forward_dir)
        self.historical_dir = Path(historical_dir)

    def _read_csv(self, path: Path, required_columns: list = None) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
            
        try:
            df = pd.read_csv(path)
            if df.empty:
                return pd.DataFrame()
                
            if required_columns:
                missing = [c for c in required_columns if c not in df.columns]
                if missing:
                    # Return empty to avoid downstream KeyError
                    return pd.DataFrame()
                    
            return df
        except Exception:
            return pd.DataFrame()

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_forward_signals(self) -> pd.DataFrame:
        cols = ["signal_id", "symbol", "signal_timestamp", "direction", "planned_entry", "stop_loss", "target", "risk_reward_ratio", "position_size", "capital_at_risk", "signal_status", "signal_reason"]
        return self._read_csv(self.forward_dir / "forward_signals.csv", cols)

    def get_forward_positions(self) -> pd.DataFrame:
        data = self._read_json(self.forward_dir / "forward_open_positions.json")
        if isinstance(data, list) and len(data) > 0:
            return pd.DataFrame(data)
        return pd.DataFrame()
        
    def get_forward_portfolio(self) -> pd.DataFrame:
        return self._read_csv(self.forward_dir / "forward_portfolio_history.csv")
        
    def get_forward_trades(self) -> pd.DataFrame:
        return self._read_csv(self.forward_dir / "forward_trades.csv")

    def get_historical_trades(self) -> pd.DataFrame:
        return self._read_csv(self.historical_dir / "walk_forward_trades.csv")
        
    def get_health_metrics(self) -> pd.DataFrame:
        return self._read_csv(self.forward_dir / "forward_runner_health.csv")
        
    def get_universe_health(self) -> pd.DataFrame:
        return self._read_csv(self.forward_dir / "forward_universe_health.csv")
