# TPQSE Repository Cleanup Audit

## Summary
The TPQSE repository has been successfully reorganized to cleanly separate the forward-testing production environment from the historical research environment. The strategy and configuration remain strictly frozen.

* **Strategy Version:** TPQSE_v1.0
* **Configuration Fingerprint:** `1fa5372a8a97e3dea6445543c844c048d2d7257c009b595681b2f0f5fd0b5327` (UNCHANGED)
* **Test Suite:** 138 PASSED / 0 FAILED / 4 SKIPPED
* **Forward Ledger Location:** `results/forward/`
* **Historical Ledger Location:** `results/historical/`

## Structural Changes

### Files Moved
The following production scripts were moved to the `forward/` directory:
* `forward_config.py` -> `forward/config.py`
* `forward_engine.py` -> `forward/engine.py`
* `daily_forward_runner.py` -> `forward/runner.py`
* `run_forward_session.py` -> `forward/session.py`
* `forward_watchdog.py` -> `forward/watchdog.py`

The following historical research scripts were moved to the `research/` directory:
* `run_walk_forward.py` -> `research/walk_forward.py`
* `run_expanded.py` -> `research/expanded_validation.py`
* `run_final_validation.py` -> `research/final_validation.py`
* `run_full_validation.py` -> `research/full_validation.py`
* `oos_boundary_audit.py` -> `research/oos_boundary_audit.py`
* `reconcile_portfolio.py` -> `research/portfolio_reconciliation.py`
* *Other historical scripts mapped appropriately.*

### Files Deleted
The following temporary / development scratch scripts were removed:
* `scratch_freshness.py`
* `generate_inventory.py`
* `scratch/audit_script.py`
* `scratch/audit_script_corrected.py`
* `scratch/position_overlap_script.py`

### Artifacts Organized
* Audits relocated to `results/audits/`
* Forward ledger artifacts initialized in `results/forward/`
* Historical research data moved to `results/historical/`

## Verifications
1. **Tests:** All tests pass, including structural checks and isolated production simulation.
2. **Imports:** Validated across all `forward/`, `research/`, and `tests/` directories.
3. **Execution Path:** The daily runner can now be executed via `python -m forward.runner`.
4. **Data Isolation:** Pytest monkeypatching correctly handles the updated module structures, preventing corruption of the `results/forward/` ledger.
