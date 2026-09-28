"""Run the full real-photo pipeline: validate -> subset -> train -> evaluate.

Assumes raw/train.parquet + raw/test.parquet are already downloaded
(see README). Full CPU training takes ~13 minutes.
"""
import subprocess
import sys

STEPS = [
    ["src/prepare_data.py", "--extract"],
    ["src/prepare_data.py", "--validate", "--no-grid"],
    ["src/build_subset.py"],
    ["src/train.py"],
    ["src/evaluate.py"],
]

for cmd in STEPS:
    print(f"\n=== {cmd[0]} {' '.join(cmd[1:])} " + "=" * 40)
    ret = subprocess.run([sys.executable, *cmd]).returncode
    if ret != 0:
        sys.exit(f"{cmd[0]} failed with exit code {ret}")
print("\nAll done. Model: models/best_model.pth | Metrics: results/")
