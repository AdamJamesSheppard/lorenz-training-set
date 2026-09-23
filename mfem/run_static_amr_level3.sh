#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
pde_prefix=/home/adam/.local/share/mamba/envs/pde
stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$repo_dir/runs/mfem-static-amr-level3/$stamp"
first="$repo_dir/runs/mfem-static-amr-reproduction/20260916T221235Z"
second="$repo_dir/runs/mfem-static-amr-level2/20260922T231219Z"
indicator="$repo_dir/runs/mature-time-aggregated-grid-pipeline/20260915T134916Z/time_aggregated_indicator.npy"
axes="$repo_dir/experiments/mature-graded-fine-axes.json"
fine="$repo_dir/runs/mature-full-spd-graded-fine-comparison/20260914T231639Z/mature_bimodal_q2_local_qp_graded58x68x56"
particles="$repo_dir/runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference/mc_final_particles.npy"
mkdir -p "$run_dir/design" "$run_dir/mfem" "$repo_dir/build/mfem-physical-equivalence"
on_exit() {
  code=$?
  if [[ $code -ne 0 && ! -f "$run_dir/static_amr_level3_comparison.json" ]]; then
    printf '{"status":"FAILED_THIRD_DEPTH_PIPELINE","exit_code":%d}\n' "$code" > "$run_dir/status.json"
  fi
}
trap on_exit EXIT
cp "$repo_dir/experiments/mfem-static-nc-hex-level3.yaml" "$run_dir/config.yaml"
git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
git -C "$repo_dir" status --short > "$run_dir/git_status.txt"
sha256sum "$indicator" "$axes" "$first/design/base_cell_marks.bin" \
  "$second/design/child_cell_marks.bin" \
  "$second/mfem/final_q2_subcell_averages.bin" \
  "$fine/final_q2_subcell_averages.npy" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" > "$run_dir/input_sha256.txt"
printf '{"status":"PREPARING_THIRD_DEPTH"}\n' > "$run_dir/status.json"

cd "$repo_dir"
"$pde_prefix/bin/python" mfem/prepare_static_amr_level3.py \
  "$indicator" "$axes" "$second/design/child_cell_marks.bin" "$run_dir/design"
export PATH="$env_prefix/bin:$PATH"
"$env_prefix/bin/mpicxx" -std=c++17 -O2 \
  -I"$env_prefix/include" -I"$pde_prefix/include/osqp" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" \
  -L"$env_prefix/lib" -L"$pde_prefix/lib" \
  -Wl,-rpath,"$env_prefix/lib" -Wl,-rpath,"$pde_prefix/lib" \
  -lmfem -lHYPRE -losqp \
  -o "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence"

printf '{"status":"RUNNING_THIRD_DEPTH","steps":320}\n' > "$run_dir/status.json"
"$env_prefix/bin/mpiexec" -n 8 \
  "$repo_dir/build/mfem-physical-equivalence/mfem_physical_equivalence" \
  amr3 45 54 54 "$first/design/base_cell_marks.bin" \
  "$second/design/child_cell_marks.bin" \
  "$run_dir/design/grandchild_cell_marks.bin" \
  "$first/design/mixture_parameters.bin" "$run_dir/mfem"

set +e
"$pde_prefix/bin/python" mfem/compare_static_amr_level3.py \
  "$run_dir" "$first" "$second" "$fine" "$particles"
code=$?
set -e
if [[ $code -eq 0 ]]; then
  printf '{"status":"PASSED_THIRD_DEPTH_VOXEL_GATES"}\n' > "$run_dir/status.json"
else
  printf '{"status":"FAILED_THIRD_DEPTH_VOXEL_GATES","exit_code":%d}\n' "$code" > "$run_dir/status.json"
fi
printf '%s\n' "$run_dir"
exit "$code"
