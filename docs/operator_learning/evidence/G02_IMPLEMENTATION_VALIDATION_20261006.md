# G02 implementation validation — 2026-10-06

Classification: software/implementation evidence only. No G02 scientific run,
computed sensitivity results, phase-A commit or gate adjudication exists yet.
Do not treat this document as a reconstruction-stability pass.

Implemented: operator_learning/reconstruction.py,
scripts/run_reconstruction_stability.py, frozen characterization configuration
and RECONSTRUCTION_STABILITY_G02_V1.md. Seven new unit tests pass (five numerical
fixtures and two predeclaration/authorization fixtures). Static ruff checks,
compilation, canonical governance consistency and git diff whitespace checks pass.
All declared source/archive input hashes were independently checked against the
prepared configuration. Fixtures use explicitly synthetic toy arrays; they do
not represent archived scientific results.

Whole-repository test attempt:87passed,1skipped,1failed MPI test before the final
two new predeclaration tests were added. Those additional two pass separately.
The two-rank launcher is blocked in this execution environment: with the matching
pde mpirun, exit213 and `pmix_ifinit: socket() failed with errno=1`, followed by
failure of the PMIx listener thread. No solver/MPI code was changed to conceal
that blocked validation; successful serial/unit checks are recorded separately.

The normal micromamba wrapper also cannot create its home-cache lock under the
current filesystem restrictions. Unit checks used the existing pde interpreter
directly: /home/adam/.local/share/mamba/envs/pde/bin/python, Python3.12.13,
NumPy2.5.2, SciPy1.18.0. No package installation/cache deletion occurred.

Dispatch blocker: Git staging failed with `Unable to create .git/index.lock:
Read-only file system`. The repository requires a clean committed predeclaration
before scientific execution. This requirement was preserved: no bypass, alternate
Git directory, uncommitted experiment or remote mutation was attempted.

Next action: restore ordinary Git write access, review/commit phase A, prepare a
fresh run and execute the CPU-only characterization. Keep G02 OPEN afterward
until a scientifically justified reconstruction-error budget and qualification
evidence are reviewed. Historical pairs and accepted population remain unchanged.

## Subsequent permission refresh and validation

After the owner enabled the unrestricted profile and requested another attempt,
Git staging succeeded. The normal ./scripts/check workflow completed with
90passed,1skipped, including successful two-rank MPI consistency. Static,
compilation, canonical-governance and whitespace checks pass. Earlier blocked
attempts remain recorded above as environment-specific historical outcomes.
The phase-A commit and fresh local dispatch are now permitted; scientific
characterization and qualification outcomes still require their own evidence.
