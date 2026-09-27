import pandas as pd

class DataLoader:
    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        raise NotImplementedError("DataLoader requires a specific vendor implementation")
