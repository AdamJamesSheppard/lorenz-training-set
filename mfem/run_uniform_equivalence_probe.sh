#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "$0")/.." && pwd)
env_prefix=/home/adam/.local/share/mamba/envs/mfem-lorenz
build_dir="$repo_dir/build/mfem-uniform-equivalence"
mkdir -p "$build_dir"
export PATH="$env_prefix/bin:$PATH"

"$env_prefix/bin/mpicxx" -std=c++17 -O2 \
  -I"$env_prefix/include" \
  "$repo_dir/mfem/mfem_uniform_equivalence_probe.cpp" \
  -L"$env_prefix/lib" -Wl,-rpath,"$env_prefix/lib" -lmfem \
  -o "$build_dir/mfem_uniform_equivalence_probe"

"$env_prefix/bin/mpiexec" -n 8 "$build_dir/mfem_uniform_equivalence_probe" "$@"
