#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
pde_prefix=/home/adam/.local/share/mamba/envs/pde
build_dir="$repo_dir/build/mfem-physical-equivalence"
nx=${1:-4}
ny=${2:-5}
nz=${3:-5}
run_dir=${4:-"$repo_dir/runs/mfem-physical-equivalence/$(date -u +%Y%m%dT%H%M%SZ)"}
mkdir -p "$build_dir" "$run_dir/mfem" "$run_dir/dolfinx"
export PATH="$env_prefix/bin:$PATH"

"$env_prefix/bin/mpicxx" -std=c++17 -O2 \
  -I"$env_prefix/include" -I"$pde_prefix/include/osqp" \
  "$repo_dir/mfem/mfem_physical_equivalence.cpp" \
  -L"$env_prefix/lib" -L"$pde_prefix/lib" \
  -Wl,-rpath,"$env_prefix/lib" -Wl,-rpath,"$pde_prefix/lib" \
  -lmfem -lHYPRE -losqp \
  -o "$build_dir/mfem_physical_equivalence"

git -C "$repo_dir" rev-parse HEAD > "$run_dir/git_commit.txt"
git -C "$repo_dir" status --short > "$run_dir/git_status.txt"
printf '%s\n' "$nx $ny $nz" > "$run_dir/mesh.txt"

"$env_prefix/bin/mpiexec" -n 8 \
  "$build_dir/mfem_physical_equivalence" "$nx" "$ny" "$nz" "$run_dir/mfem"

cd "$repo_dir"
./scripts/run-in-env mpiexec -n 8 python mfem/dolfinx_physical_equivalence.py \
  "$nx" "$ny" "$nz" "$run_dir/dolfinx"

set +e
./scripts/run-in-env python mfem/compare_physical_equivalence.py \
  "$run_dir" "$nx" "$ny" "$nz"
result=$?
set -e
printf '%s\n' "$result" > "$run_dir/exit_code.txt"
printf '%s\n' "$run_dir"
exit "$result"
