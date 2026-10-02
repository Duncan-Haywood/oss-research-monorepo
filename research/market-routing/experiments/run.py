"""Runs switching.py in order; stdout is experiments/results.txt. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for script in ("switching.py",):
    print(f"==== experiments/{script}", flush=True)
    runpy.run_path(str(HERE / script), run_name="__main__")
    sys.stdout.flush()
