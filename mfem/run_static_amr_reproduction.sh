#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
pde_prefix=/home/adam/.local/share/mamba/envs/pde
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$repo_dir/runs/mfem-static-amr-reproduction/$stamp"
indicator="$repo_dir/runs/mature-time-aggregated-grid-pipeline/20260915T134916Z/time_aggregated_indicator.npy"
axes="$repo_dir/experiments/mature-graded-fine-axes.json"
mixture="$repo_dir/runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference/mature_mixture.json"
fine="$repo_dir/runs/mature-full-spd-graded-fine-comparison/20260914T231639Z/mature_bimodal_q2_local_qp_graded58x68x56"
particles="$repo_dir/runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference/mc_final_particles.npy"
mkdir -p "$run_dir/design" "$run_dir/mfem" "$repo_dir/build/mfem-physical-equivalence"
on_exit() {
  code=$?
  if [[ $code -ne 0 && ! -f "$run_dir/static_amr_comparison.json" ]]; then
    printf '{"status":"FAILED_STATIC_AMR_PIPELINE","exit_code":%d}\n' "$code" > "$run_dir/status.json"
  fi
}
trap on_exit EXIT
cp "$repo_dir/experiments/mfem-static-nc-hex-reproduction.yaml" "$run_dir/config.yaml"
git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
git -C "$repo_dir" status --short > "$run_dir/git_status.txt"
sha256sum "$indicator" "$axes" "$mixture" "$fine/final_q2_subcell_averages.npy" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" > "$run_dir/input_sha256.txt"
printf '{"status":"PREPARING_STATIC_AMR"}\n' > "$run_dir/status.json"

cd "$repo_dir"
./scripts/run-in-env python mfem/prepare_static_amr.py \
  "$indicator" "$axes" "$mixture" "$run_dir/design"
export PATH="$env_prefix/bin:$PATH"
"$env_prefix/bin/mpicxx" -std=c++17 -O2 \
  -I"$env_prefix/include" -I"$pde_prefix/include/osqp" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" \
  -L"$env_prefix/lib" -L"$pde_prefix/lib" \
  -Wl,-rpath,"$env_prefix/lib" -Wl,-rpath,"$pde_prefix/lib" \
  -lmfem -lHYPRE -losqp \
  -o "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence"

printf '{"status":"RUNNING_STATIC_AMR_MATURE_TRAJECTORY","steps":320}\n' > "$run_dir/status.json"
"$env_prefix/bin/mpiexec" -n 8 \
  "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence" \
  amr 45 54 54 "$run_dir/design/base_cell_marks.bin" \
  "$run_dir/design/mixture_parameters.bin" "$run_dir/mfem"

set +e
./scripts/run-in-env python mfem/compare_static_amr.py "$run_dir" "$fine" "$particles"
code=$?
set -e
if [[ $code -eq 0 ]]; then
  printf '{"status":"PASSED_STATIC_AMR_REPRODUCTION_GATES"}\n' > "$run_dir/status.json"
else
  printf '{"status":"FAILED_STATIC_AMR_REPRODUCTION_GATES","exit_code":%d}\n' "$code" > "$run_dir/status.json"
fi
printf '%s\n' "$run_dir"
exit "$code"
