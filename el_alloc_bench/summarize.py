#!/usr/bin/env python3
# Per-step time ((wall at 220 steps - wall at 20 steps) / 200), start-up time and peak GPU memory per label, from results.csv.
import csv
import os
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.csv")
runs = defaultdict(dict)
for row in csv.DictReader(open(path)):
    if row["wall_s"] != "FAIL" and row["steps"] in ("20", "220"):
        runs[(int(row["ranks"]), float(row["np"]), row["label"])][int(row["steps"])] = (float(row["wall_s"]), row["peak_mem_mib"])

labels = sorted({k[2] for k in runs})
print(f"{'ranks':>5} {'particles':>10} " + " ".join(f"{l + ' ms/step':>16} {l + ' init s':>12} {l + ' MiB':>10}" for l in labels))
for ranks, np in sorted({k[:2] for k in runs}):
    cols = []
    for l in labels:
        r = runs.get((ranks, np, l), {})
        if 20 in r and 220 in r:
            step = (r[220][0] - r[20][0]) / 200
            cols.append(f"{1e3 * step:16.2f} {r[20][0] - 20 * step:12.1f} {r[220][1]:>10}")
        else:
            cols.append(f"{'-':>16} {'-':>12} {'-':>10}")
    print(f"{ranks:5d} {np:10.0f} " + " ".join(cols))
