# Operator-learning architecture and boundaries

New dependency-free governance lives in operator_learning/governance.py.
NumPy-only representations, metrics and diagnostic baselines live in
operator_learning/numerics.py. They import no FEM, MPI, PETSc, Torch or solver
runtime. CLI scripts expose checks, predeclaration freeze and historical audit.

Historical implementations stay in place: mfem/run_neural_pilot.py produces
targets and invokes scripts/train_neural_pilot.py in its isolated Torch runtime.
This coupled legacy entry point is guarded against relaunch under the new
programme. The old source is recoverable at 11d222f and the completed run remains
unchanged. Build scripts, raw GMM fixtures and solver algorithms are preserved.

New scientific learning consumers must accept a sealed dataset manifest and
operate read-only on inputs, with their own new run/checkpoint directory.
No import of the FEM generator or implicit compile/run is permitted.
Orchestration is explicit and separately authorized.

Candidates: mandatory learned linear and reduced POD/PCA linear propagation,
persistence and nearest-neighbour diagnostics, modest convolutional model and
FNO; alternatives need reasons and comparable budgets. Full linear/POD training
and new models are deferred until distributions/representation are specified.
Do not create empty distributions/datasets/models subpackages merely for symmetry.

Representations support conservative averaging and physical-volume metrics.
Metric definitions and lobe/boundary regions must be frozen in configs.
CPU/GPU fixtures test software, not density accuracy. Fast GitHub CI checks
governance and tiny NumPy examples; optional Torch fixtures test the historical
model separately. Multi-hour targets and serious training remain explicit runs.
