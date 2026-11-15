"""Aggregate results/*.json run files into a single comparison table.

Prints a markdown table (clean F1, morphed F1, robustness gap, params) and writes
results/comparison.md. Point it at the run tags produced by src.train.train.

Usage:
    python -m src.eval.compare
"""
from __future__ import annotations

import glob
import json
import os

from src.eval.common import RESULTS_DIR

# Non-run JSONs to skip.
SKIP = {"robustness_sweep.json", "embedding_metrics.json", "fewshot.json"}


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json"))):
        if os.path.basename(path) in SKIP:
            continue
        with open(path) as f:
            r = json.load(f)
        if "clean_f1" not in r:
            continue
        rows.append(r)

    if not rows:
        print("No run results found in results/.")
        return

    rows.sort(key=lambda r: r["clean_f1"], reverse=True)
    header = f"| {'run':32s} | enc | clean F1 | morph F1 | gap | params |"
    sep = "|" + "-" * 34 + "|-----|----------|----------|-------|--------|"
    lines = [header, sep]
    for r in rows:
        lines.append(
            f"| {r['tag']:32s} | {r['encoder']:>3s} | "
            f"{r['clean_f1']:.3f}    | {r['morph_f1']:.3f}    | "
            f"{r['robustness_gap_f1']:+.3f} | {r['params']:>6,} |"
        )
    table = "\n".join(lines)
    print(table)

    with open(os.path.join(RESULTS_DIR, "comparison.md"), "w") as f:
        f.write("# Model comparison\n\n" + table + "\n")
    print(f"\nsaved {os.path.join(RESULTS_DIR, 'comparison.md')}")


if __name__ == "__main__":
    main()
