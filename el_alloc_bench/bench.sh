#!/usr/bin/env bash
# A/B benchmark of the particle arrays. Run inside a GPU allocation with the GPU environment loaded.
# Usage: bench.sh <mfc_checkout> <label> [ranks ...]    e.g. bench.sh ../MFC-EL-phase1 base 1 2 4
# BENCH_NPS sets the particle counts (default "1e5 1e6 4e6"); BENCH_GRID scales the 200x100x100 grid.
set -uo pipefail
mfc=$(cd "$1" && pwd); label=$2; shift 2
ranks=${*:-1 2 4}
nps=${BENCH_NPS:-1e5 1e6 4e6}
here=$(cd "$(dirname "$0")" && pwd)
csv=$here/results.csv
[ -f "$csv" ] || echo "label,ranks,np,steps,wall_s,peak_mem_mib" > "$csv"

for r in $ranks; do
    for np in $nps; do
        dir=$here/runs/$label-r$r-np$np
        rm -rf "$dir"; mkdir -p "$dir"; cp "$here/case.py" "$dir/"
        export BENCH_NP=$np
        if ! BENCH_STEPS=20 "$mfc/mfc.sh" run "$dir/case.py" -t pre_process -n "$r" -b mpirun --no-build > "$dir/pre.log" 2>&1; then
            echo "$label,$r,$np,pre_process,FAIL," | tee -a "$csv"; continue
        fi
        for steps in 20 220; do
            export BENCH_STEPS=$steps
            nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -lms 200 > "$dir/mem_$steps.log" &
            smi=$!
            t0=$(date +%s.%N)
            if "$mfc/mfc.sh" run "$dir/case.py" -t simulation -n "$r" -b mpirun --no-build > "$dir/sim_$steps.log" 2>&1; then
                wall=$(awk "BEGIN{print $(date +%s.%N) - $t0}")
            else
                wall=FAIL
            fi
            kill $smi; wait $smi 2>/dev/null
            echo "$label,$r,$np,$steps,$wall,$(sort -n "$dir/mem_$steps.log" | tail -1)" | tee -a "$csv"
        done
    done
done
