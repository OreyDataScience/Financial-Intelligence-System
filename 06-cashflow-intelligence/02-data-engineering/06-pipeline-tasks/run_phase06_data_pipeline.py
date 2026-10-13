"""
Phase 06 - Data pipeline runner
Orey Analytics - Cash Flow Intelligence

Runs the 01-data pipeline end to end, in order:

    1. 01-ingestion/generate_raw_data.py         -> 01-data/01-raw
    2. 02-cleaning/clean_and_validate.py         -> 01-data/02-staging
    3. 03-transformation/reconcile_and_process.py -> 01-data/03-processed

Raw data is immutable, so step 1 is skipped when raw files already exist.
Pass --regenerate to rebuild the synthetic raw dataset from scratch.

Scheduling / orchestration of this runner belongs in 16-orchestration;
this file only holds the "what runs, in what order" logic.

Usage (from anywhere):
    python run_phase06_data_pipeline.py
    python run_phase06_data_pipeline.py --regenerate
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# This file lives at: 02-data-engineering/06-pipeline-tasks/run_phase06_data_pipeline.py
_ENGINEERING_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _ENGINEERING_DIR.parent

GENERATE = _ENGINEERING_DIR / "01-ingestion" / "generate_raw_data.py"
CLEAN = _ENGINEERING_DIR / "02-cleaning" / "clean_and_validate.py"
RECONCILE = _ENGINEERING_DIR / "03-transformation" / "reconcile_and_process.py"
RAW_MARKER = _PROJECT_ROOT / "01-data" / "01-raw" / "business_profiles_raw.csv"


def run_step(label, script, extra_args=()):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}", flush=True)
    start = time.time()
    result = subprocess.run([sys.executable, str(script), *extra_args])
    if result.returncode != 0:
        print(f"\nFAILED: {label} (exit code {result.returncode}). Pipeline stopped.")
        sys.exit(result.returncode)
    print(f"\n[{label}] finished in {time.time() - start:.1f}s", flush=True)


def main(regenerate):
    if regenerate or not RAW_MARKER.exists():
        run_step("Step 1/3 - Generate synthetic raw data (01-raw)", GENERATE,
                 ["--force"] if regenerate else [])
    else:
        print("Step 1/3 - Raw data already exists in 01-raw (immutable) - skipping generation.\n"
              "           Use --regenerate to rebuild it.")

    run_step("Step 2/3 - Clean, standardize and flag (02-staging)", CLEAN)
    run_step("Step 3/3 - Reconcile and process (03-processed)", RECONCILE)
    print("\nPhase 06 data pipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Phase 06 01-data pipeline end to end.")
    parser.add_argument("--regenerate", action="store_true",
                        help="Regenerate (overwrite) the synthetic raw dataset first")
    main(parser.parse_args().regenerate)
