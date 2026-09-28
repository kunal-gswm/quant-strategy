"""
Shared pytest configuration for forward-test isolation.

Sets FORWARD_RESULTS_DIR to a temporary directory before any forward_engine
imports, ensuring tests never write to the production results/ directory.
"""
import pytest
import os
import shutil
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True, scope="function")
def isolated_results_dir(tmp_path, monkeypatch):
    """
    Redirect all forward-engine output to a per-test temporary directory.
    This prevents any test from polluting the production results/ directory.
    """
    test_results = tmp_path / "test_results"
    test_results.mkdir(parents=True, exist_ok=True)
    snapshots = test_results / "forward_universe_snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)

    # Patch the environment variable
    monkeypatch.setenv("FORWARD_RESULTS_DIR", str(test_results))

    # Patch the module-level RESULTS_DIR in forward_engine (already imported)
    import forward_engine
    monkeypatch.setattr(forward_engine, "RESULTS_DIR", test_results)
    monkeypatch.setattr(forward_engine, "SNAPSHOT_DIR", snapshots)

    # Also patch in forward_watchdog if imported
    try:
        import forward_watchdog
        monkeypatch.setattr(forward_watchdog, "RESULTS_DIR", test_results)
    except (ImportError, AttributeError):
        pass

    # Also patch in run_forward_session if imported
    try:
        import run_forward_session
        # run_forward_session imports RESULTS_DIR from forward_engine at module level
        # so we need to patch it there too if it has a local reference
    except (ImportError, AttributeError):
        pass

    yield test_results
