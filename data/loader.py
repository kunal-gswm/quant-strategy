import os
import pandas as pd
import yfinance as yf
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache"


class DataLoader:
    """Loads daily OHLCV data from Yahoo Finance (NSE/BSE tickers).

    Supports automatic CSV caching so that repeated runs are
    deterministic and don't hit the network.  Cache files are keyed by
    ``{symbol}_{start}_{end}.csv``.

    Usage
    -----
    >>> loader = DataLoader()
    >>> df = loader.load("RELIANCE.NS", "2020-01-01", "2024-12-31")
    >>> df.columns  # ['open', 'high', 'low', 'close', 'volume']
    """

    def __init__(self, cache_dir: str | Path | None = None, use_cache: bool = True):
        self.cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self.use_cache = use_cache
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── public API ──────────────────────────────────────────────────
    def load(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Return a DatetimeIndex DataFrame with columns
        [open, high, low, close, volume]."""
        cache_path = self._cache_path(symbol, start, end)

        if self.use_cache and cache_path.exists():
            df = self._read_csv(cache_path)
            print(f"[DataLoader] Loaded {len(df)} bars from cache: {cache_path.name}")
            return df

        df = self._fetch_yfinance(symbol, start, end)

        if self.use_cache:
            df.to_csv(cache_path)
            print(f"[DataLoader] Cached {len(df)} bars -> {cache_path.name}")

        return df

    def load_csv(self, filepath: str | Path) -> pd.DataFrame:
        """Load OHLCV from an arbitrary CSV (must have columns
        date/timestamp, open, high, low, close, volume)."""
        return self._read_csv(Path(filepath))

    # ── Yahoo Finance fetcher ───────────────────────────────────────
    @staticmethod
    def _fetch_yfinance(symbol: str, start: str, end: str) -> pd.DataFrame:
        print(f"[DataLoader] Downloading {symbol} from Yahoo Finance ({start} -> {end}) ...")
        ticker = yf.Ticker(symbol)
        raw = ticker.history(start=start, end=end, auto_adjust=True)

        if raw.empty:
            raise ValueError(
                f"yfinance returned no data for '{symbol}'. "
                "Check the ticker (e.g. RELIANCE.NS for NSE, RELIANCE.BO for BSE)."
            )

        df = raw.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })[["open", "high", "low", "close", "volume"]].copy()

        df.index.name = "date"
        # Strip timezone info so downstream code doesn't need to care
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        return df

    # ── CSV helpers ─────────────────────────────────────────────────
    @staticmethod
    def _read_csv(path: Path) -> pd.DataFrame:
        df = pd.read_csv(path, parse_dates=[0], index_col=0)
        # Normalise column names to lowercase
        df.columns = [c.strip().lower() for c in df.columns]
        expected = {"open", "high", "low", "close", "volume"}
        missing = expected - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}")
        return df[["open", "high", "low", "close", "volume"]]

    def _cache_path(self, symbol: str, start: str, end: str) -> Path:
        safe = symbol.replace(".", "_").replace("/", "_")
        return self.cache_dir / f"{safe}_{start}_{end}.csv"
