#!/usr/bin/env bash
# A/B benchmark of the particle arrays. Run inside a GPU allocation with the GPU environment loaded.
# Usage: bench.sh <mfc_checkout> <label> [ranks ...]    e.g. bench.sh ../MFC-EL-phase1 base 1 2 4
# BENCH_NPS sets the particle counts (default "1e5 1e6 4e6"); BENCH_GRID scales the 200x100x100 grid.
# BENCH_RUN_ARGS are the launcher arguments for ./mfc.sh run (default "-b mpirun"; on Tuolumne use "-c tuo").
set -uo pipefail
mfc=$(cd "$1" && pwd); label=$2; shift 2
ranks=${*:-1 2 4}
nps=${BENCH_NPS:-1e5 1e6 4e6}
run_args=${BENCH_RUN_ARGS:--b mpirun}
here=$(cd "$(dirname "$0")" && pwd)

# ./mfc.sh must run from the checkout's root
mfc_run() { (cd "$mfc" && ./mfc.sh run "$@"); }

# Print the used device memory (MiB) of every GPU every 0.2 s: nvidia-smi on NVIDIA, rocm-smi on AMD
sample_gpu_mem() {
    if nvidia-smi -L > /dev/null 2>&1; then
        nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -lms 200
    else
        while true; do
            rocm-smi --showmeminfo vram --csv 2> /dev/null | awk -F, 'NR > 1 && $3 ~ /^[0-9]+$/ {print int($3/1048576)}'
            sleep 0.2
        done
    fi
}
csv=$here/results.csv
[ -f "$csv" ] || echo "label,ranks,np,steps,wall_s,peak_mem_mib" > "$csv"

for r in $ranks; do
    for np in $nps; do
        dir=$here/runs/$label-r$r-np$np
        rm -rf "$dir"; mkdir -p "$dir"; cp "$here/case.py" "$dir/"
        export BENCH_NP=$np
        if ! BENCH_STEPS=20 mfc_run "$dir/case.py" -t pre_process -n "$r" $run_args --no-build > "$dir/pre.log" 2>&1; then
            echo "$label,$r,$np,pre_process,FAIL," | tee -a "$csv"; continue
        fi
        for steps in 20 220; do
            export BENCH_STEPS=$steps
            sample_gpu_mem > "$dir/mem_$steps.log" &
            smi=$!
            t0=$(date +%s.%N)
            if mfc_run "$dir/case.py" -t simulation -n "$r" $run_args --no-build > "$dir/sim_$steps.log" 2>&1; then
                wall=$(awk "BEGIN{print $(date +%s.%N) - $t0}")
            else
                wall=FAIL
            fi
            kill $smi; wait $smi 2>/dev/null
            echo "$label,$r,$np,$steps,$wall,$(grep -E '^[0-9]+$' "$dir/mem_$steps.log" | sort -n | tail -1)" | tee -a "$csv"
        done
    done
done
