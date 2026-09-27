from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class HistoricalUniverseConfig:
    source: str | None = None
    dataset_path: str | Path | None = None
    required_columns: tuple[str, ...] = (
        "symbol",
        "date",
        "is_constituent",
        "index_name",
    )
    notes: str = (
        "Historical Nifty 500 constituent membership is not available in the current repository. "
        "This interface exists so a point-in-time historical constituent dataset can be attached later "
        "without changing the live strategy logic."
    )


def get_historical_universe() -> list[dict] | None:
    """Return a historical constituent table when an actual dataset is present.

    The current workspace does not include a reliable historical constituent source, so this
    function intentionally returns None until a valid point-in-time source is added.
    """
    return None


def load_historical_universe(path: str | Path | None = None) -> list[dict] | None:
    """Load a historical universe file when one is provided by the user or by the environment.

    This is a placeholder for future support of point-in-time membership datasets from NSE,
    CMIE Prowess, or commercial providers.
    """
    if path is None:
        return get_historical_universe()

    target = Path(path)
    if not target.exists():
        return None

    # Deferred implementation; this keeps the project able to accept a concrete dataset later
    # without altering the strategy or backtest engine.
    return None
