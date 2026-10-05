# Repository map

Generated: 2026-10-05T20:44:02+01:00

```text
docs/ACTIVE_TASK.md
docs/ARCHITECTURE.md
docs/CLAIMS.md
docs/DECISIONS.md
docs/DENSITY_VISUALIZATION.md
docs/MATHEMATICAL_SPEC.md
docs/MATH_PROTOCOL.md
docs/NEURAL_PILOT.md
docs/NEURAL_PILOT_WORKFLOW.md
docs/PROJECT_STATE.md
docs/REFERENCES.md
docs/RESEARCH_DIRECTIONS.md
docs/assumptions.yaml
docs/generated/REPO_MAP.md
docs/history/PROJECT_STATE_before_operator_learning_20261005.md
docs/operator_learning/ARCHITECTURE.md
docs/operator_learning/CLAIMS.md
docs/operator_learning/DATA_CONTRACT.md
docs/operator_learning/DECISIONS.md
docs/operator_learning/DISTRIBUTION_CONTRACT.md
docs/operator_learning/FEM_GOVERNANCE_RECONSTRUCTION.md
docs/operator_learning/GATES.md
docs/operator_learning/GOVERNANCE.md
docs/operator_learning/PROBLEM.md
docs/operator_learning/PROJECT_STATE.md
docs/operator_learning/README.md
docs/operator_learning/RISKS.md
docs/operator_learning/assumptions.yaml
docs/operator_learning/evidence/PILOT_20261004T133438Z.json
docs/operator_learning/evidence/README.md
docs/operator_learning/evidence/seals.json
docs/operator_learning/gates.json
docs/operator_learning/generators.json
docs/operator_learning/state.json
docs/releases/v0.1.0.md
docs/releases/v0.2.0.md
docs/solver_monograph/README.md
docs/solver_monograph/bibliography.tex
docs/solver_monograph/book.tex
docs/solver_monograph/development.tex
docs/solver_monograph/discretisation.tex
docs/solver_monograph/foundations.tex
docs/solver_monograph/history_appendix.tex
docs/solver_monograph/implementation.tex
docs/solver_monograph/ledger_appendix.tex
docs/solver_monograph/manifest.json
docs/solver_monograph/source_ledger.json
docs/solver_monograph/technical_appendices.tex
docs/tasks/TASK_TEMPLATE.md
experiments/corrected-q2-crank-nicolson.yaml
experiments/local-q2-cn-full-spd-controlled.yaml
experiments/local-q2-cn-full-spd-spatial-refinement.yaml
experiments/local-q2-cn-spatial-refinement.yaml
experiments/local-q2-cn-tight-ksp-refinement.yaml
experiments/local-q2-crank-nicolson.yaml
experiments/local-q2-optimizer-validation.yaml
experiments/local-q2-osqp-profile.yaml
experiments/local-q2-positivity-projection.yaml
experiments/mature-afc-update.yaml
experiments/mature-dof-convex-diagnostic.yaml
experiments/mature-graded-fine-axes.json
experiments/mature-graded-fine-comparison.yaml
experiments/mature-graded-static-axes.json
experiments/mature-graded-static-comparison.yaml
experiments/mature-positivity-certificate-diagnostic.yaml
experiments/mature-state-decision.yaml
experiments/mature-time-aggregated-level3-pipeline.yaml
experiments/mature-uniform60-reference.yaml
experiments/method-selection-research.yaml
experiments/mfem-broader-support.yaml
experiments/mfem-domain-sensitivity.yaml
experiments/mfem-mature-half-timestep.yaml
experiments/mfem-mature-uniform-equivalence.yaml
experiments/mfem-physical-equivalence-gate.yaml
experiments/mfem-static-nc-hex-level2.yaml
experiments/mfem-static-nc-hex-level3.yaml
experiments/mfem-static-nc-hex-reproduction.yaml
experiments/mfem-support-depth.yaml
experiments/mfem-support-sensitivity.yaml
experiments/mfem-uniform-equivalence-gate.yaml
experiments/neural-pilot.json
experiments/operator_learning/OL-G00_alignment_v1.json
experiments/same-mesh-q2-corrected.yaml
experiments/same-mesh-q2-falsification.yaml
experiments/same-mesh-q2-timestep.yaml
experiments/smoke-forecast.yaml
experiments/unlimited-q2-crank-nicolson.yaml
experiments/unlimited-q2-timestep-attribution.yaml
lorenz_fpe/__init__.py
lorenz_fpe/afc.py
lorenz_fpe/core.py
lorenz_fpe/dataset.py
lorenz_fpe/finite_volume.py
lorenz_fpe/local_projection.py
lorenz_fpe/validation.py
operator_learning/__init__.py
operator_learning/governance.py
operator_learning/numerics.py
scripts/audit_operator_pilot.py
scripts/bootstrap
scripts/build-pilot-solver
scripts/build_solver_monograph_evidence.py
scripts/check
scripts/check_neural_pilot_gpu.py
scripts/check_operator_learning.py
scripts/context
scripts/package_solver_monograph.py
scripts/plot_saved_density.py
scripts/prepare_operator_run.py
scripts/repo-map
scripts/run-experiment
scripts/run-in-env
scripts/run_experiment.py
scripts/setup-neural-pilot-gpu
scripts/train_neural_pilot.py
scripts/verify-math
scripts/verify_math.py
scripts/verify_solver_monograph.py
tests/__init__.py
tests/mpi_probe_worker.py
tests/operator_learning/test_governance.py
tests/operator_learning/test_historical_evidence.py
tests/operator_learning/test_legacy_contract.py
tests/operator_learning/test_model_optional.py
tests/operator_learning/test_numerics.py
tests/test_accuracy_repairs.py
tests/test_limiter.py
tests/test_memory_backpressure.py
tests/test_mfem_mature_compare.py
tests/test_mpi_consistency.py
tests/test_neural_pilot_export.py
tests/test_solver_smoke.py
tests/test_spatial_experiment.py
tests/test_validation.py
./METHOD_SELECTION_REPORT.md
./NUMERICAL_METHOD.md
./POSITIVITY_AUDIT.md
./PRODUCTION_READINESS.md
./README.md
./benchmark_scaling.py
./boundary_flux_report.json
./build_experiment_manifest.py
./corrected_q2_crank_nicolson_report.json
./crank_nicolson_mc_20x24x24.json
./experiment_manifest.json
./generate_dataset.py
./high_resolution_monte_carlo_report.json
./higher_order_report.json
./independent_reference_refined_report.json
./independent_reference_report.json
./independent_reference_study.py
./limiter_impact_20x24x24.json
./local_projection_optimizer_study.py
./local_projection_study.py
./local_q2_dynamic_projection_report.json
./local_q2_full_spd_control_report.json
./local_q2_full_spd_spatial_report.json
./local_q2_mature_bimodal_report.json
./local_q2_optimizer_validation_report.json
./local_q2_positivity_projection_report.json
./local_q2_projection_performance_report.json
./local_q2_spatial_refinement_report.json
./local_q2_tight_refinement_report.json
./mature_da_projected_report.json
./mature_da_report.json
./mature_da_study.py
./mature_dof_convex_diagnostic.py
./mature_forecast_validation.json
./mature_forecast_validation.py
./mature_graded_efficiency_report.json
./mature_graded_fine_report.json
./mature_positivity_certificate_diagnostic_report.json
./mature_positivity_diagnostic.py
./mature_time_aggregated_pipeline.py
./mc_timestep_repair.py
./mc_timestep_same_initial_law.json
./method_selection_report.json
./monte_carlo_fixed_dt_20x24x24.json
./monte_carlo_uncertainty_20x24x24.json
./monte_carlo_uncertainty_30x36x36.json
./q1_fine_bayesian_update_report.json
./q2_bayesian_update_report.json
./q2_bayesian_update_subcell_report.json
./q2_common_law_monte_carlo.json
./q2_common_law_subcell_monte_carlo.json
./resplit_dataset.py
./same_mesh_q2_corrected_report.json
./same_mesh_q2_falsification_report.json
./same_mesh_q2_study.py
./scaling_30_rank1.json
./scaling_30_rank8.json
./scaling_q2_20_rank1.json
./scaling_q2_20_rank8.json
./scaling_rank1.json
./scaling_rank2.json
./scaling_rank4.json
./scaling_rank8.json
./separate_convergence_report.json
./solver.py
./unlimited_q2_crank_nicolson_report.json
./unlimited_q2_timestep_report.json
./validate.py
./validation_repair.py
./validation_repair_report.json
./validation_report.json
./voxel_projection_20x24x24.json
```

## Python symbols
./mature_forecast_validation.py:11:def sample_q1(solver,state,n,rng):
./mature_forecast_validation.py:23:def main():
./mature_positivity_diagnostic.py:21:def _mixture_state(solver, path: Path, quadrature_degree: int) -> DensityState:
./mature_positivity_diagnostic.py:34:def _classification(solver, state: DensityState, depth: int) -> tuple[dict[str,int],list[str]]:
./mature_positivity_diagnostic.py:45:def _distribution_change(solver, raw: DensityState, corrected: DensityState) -> dict[str,object]:
./mature_positivity_diagnostic.py:79:def _evaluate_snapshot(solver, raw: DensityState, label: str,
./mature_positivity_diagnostic.py:126:def main() -> int:
./mature_time_aggregated_pipeline.py:35:def sha256(path: Path) -> str:
./mature_time_aggregated_pipeline.py:43:def run_logged(command: list[str], log: Path) -> None:
./mature_time_aggregated_pipeline.py:54:def normalized(values: np.ndarray) -> np.ndarray:
./mature_time_aggregated_pipeline.py:59:def aggregate_indicators(snapshot_dir: Path) -> tuple[np.ndarray,dict[str,object]]:
./mature_time_aggregated_pipeline.py:86:def _axis_band(
./mature_time_aggregated_pipeline.py:105:def _edges_for_band(lo: int, hi: int, common_cells: int) -> list[int]:
./mature_time_aggregated_pipeline.py:114:def design_axes(aggregate: np.ndarray) -> tuple[dict[str,object],tuple[int,int,int]]:
./mature_time_aggregated_pipeline.py:160:def generated_config(axis_path: Path, cells: tuple[int,int,int]) -> dict[str,object]:
./mature_time_aggregated_pipeline.py:216:def main() -> int:
./same_mesh_q2_study.py:31:def _sha256(path: Path) -> str:
./same_mesh_q2_study.py:39:def _model(noise_matrix: list[float] | tuple[float, ...] | None) -> Lorenz63Model:
./same_mesh_q2_study.py:46:def _marginal_tv(cell_averages: np.ndarray, particles: np.ndarray,
./same_mesh_q2_study.py:59:def _sample_truncated_gaussian(
./same_mesh_q2_study.py:84:def _sample_truncated_mixture(
./same_mesh_q2_study.py:112:def _symmetric_mature_mixture(
./same_mesh_q2_study.py:159:def _condition_mixture_on_z(
./same_mesh_q2_study.py:189:def _lobe_probabilities_grid(cell_averages: np.ndarray, domain: Domain) -> dict[str,float]:
./same_mesh_q2_study.py:197:def _lobe_probabilities_particles(particles: np.ndarray) -> dict[str,float]:
./same_mesh_q2_study.py:202:def _coarsen_averages(values: np.ndarray, shape: tuple[int,int,int]) -> np.ndarray:
./same_mesh_q2_study.py:211:def _joint_density_comparison(
./same_mesh_q2_study.py:227:def _write_indicator_snapshot(
./same_mesh_q2_study.py:298:def prepare_reference(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:413:def run_forecast(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:743:def recover_final(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:782:def parser() -> argparse.ArgumentParser:
./build_experiment_manifest.py:58:def sha256(path: Path) -> str:
./build_experiment_manifest.py:66:def git_revision() -> str | None:
./build_experiment_manifest.py:76:def extract_configuration(path: Path) -> dict[str, object]:
./build_experiment_manifest.py:85:def command_output(command: list[str]) -> str | None:
./build_experiment_manifest.py:92:def main() -> None:
./local_projection_optimizer_study.py:18:def _sha256(path: Path) -> str:
./local_projection_optimizer_study.py:26:def _terminal_problems(
./local_projection_optimizer_study.py:48:def _random_problems(
./local_projection_optimizer_study.py:61:def run(args: argparse.Namespace) -> None:
./local_projection_optimizer_study.py:200:def parser() -> argparse.ArgumentParser:
./mature_dof_convex_diagnostic.py:20:def _simplex_projection(values: np.ndarray, target: float, lower: float) -> np.ndarray:
./mature_dof_convex_diagnostic.py:40:def _repair_cell_averages(solver, raw: DensityState) -> tuple[DensityState,np.ndarray]:
./mature_dof_convex_diagnostic.py:67:def _dof_convex_limit(solver, raw: DensityState) -> tuple[DensityState,dict[str,object]]:
./mature_dof_convex_diagnostic.py:113:def _evaluate(solver,raw: DensityState,label: str) -> dict[str,object] | None:
./mature_dof_convex_diagnostic.py:144:def main() -> int:
./local_projection_study.py:21:def _sha256(path: Path) -> str:
./local_projection_study.py:29:def _marginal_tv(
./local_projection_study.py:44:def _difference_report(
./local_projection_study.py:66:def run(args: argparse.Namespace) -> None:
./local_projection_study.py:204:def parser() -> argparse.ArgumentParser:
./mature_da_study.py:11:def tensor_stats(a,domain):
./mature_da_study.py:28:def main():
tests/test_validation.py:4:class TestAnalyticBenchmarks(unittest.TestCase):
tests/test_validation.py:6:    def setUpClass(cls):
tests/test_validation.py:8:    def test_pure_diffusion(self):
tests/test_validation.py:12:    def test_constant_advection_diffusion(self):
tests/test_validation.py:16:    def test_non_gaussian(self):
scripts/verify_solver_monograph.py:18:def main():
lorenz_fpe/validation.py:19:def _correlation(cov: np.ndarray) -> np.ndarray:
lorenz_fpe/validation.py:24:def covariance_accuracy(pde_covariance: np.ndarray, samples: np.ndarray, seed: int,
lorenz_fpe/validation.py:58:class ConstantModel:
lorenz_fpe/validation.py:63:    def diffusion(self):
lorenz_fpe/validation.py:65:    def drift_numpy(self,x):
lorenz_fpe/validation.py:67:    def drift_ufl(self,x):
lorenz_fpe/validation.py:73:def gaussian_errors(solver:FokkerPlanckSolver,state,mean,covariance)->dict[str,float]:
lorenz_fpe/validation.py:81:def gaussian_representation_metrics(solver:FokkerPlanckSolver,state,mean,covariance,
lorenz_fpe/validation.py:105:def initialization_representation_study(
lorenz_fpe/validation.py:140:def _propagate_particles(model,particles,t_final,dt,rng):
lorenz_fpe/validation.py:147:def same_initial_law_monte_carlo(cells=(20,24,24),dt=.000625,t_final=.05,
lorenz_fpe/validation.py:186:def analytic_bayesian_update_study(
lorenz_fpe/validation.py:211:def manufactured_total_flux_boundary(
lorenz_fpe/validation.py:254:def higher_order_convergence_study(dt=.000625,t_final=.01,quadrature_degree=14)->dict[str,object]:
lorenz_fpe/validation.py:295:def independent_reference_and_mc_density_study(
lorenz_fpe/validation.py:347:    def density_comparison(a,b):
lorenz_fpe/validation.py:402:def common_initial_law_mc_timestep_sensitivity(
lorenz_fpe/validation.py:430:def analytic_benchmarks(cells=(8,8,8),dt=.005,t_final=.02)->dict[str,object]:
lorenz_fpe/validation.py:452:def monte_carlo_lorenz(cells=(20,24,24),dt=.00125,t_final=.05,n_particles=100000,seed=2026,
lorenz_fpe/validation.py:496:def monte_carlo_time_step_check(n_particles=30000,t_final=.05,coarse_dt=.00025,seed=6611)->dict[str,object]:
lorenz_fpe/validation.py:511:def convergence_study()->dict[str,object]:
lorenz_fpe/validation.py:558:def limiter_impact(cells=(12,16,16),dt=.0025,t_final=.05)->dict[str,object]:
lorenz_fpe/validation.py:588:def voxel_projection_validation(cells=(12,16,16),dt=.0025,t_final=.05)->dict[str,object]:
lorenz_fpe/validation.py:637:def weighted_particle_da(cells=(20,24,24),dt=.00125,t_final=.05,n_particles=50000,seed=4401)->dict[str,object]:
lorenz_fpe/validation.py:676:def domain_sensitivity()->dict[str,object]:
lorenz_fpe/validation.py:691:def run_validation(output:Path)->dict[str,object]:
scripts/verify_math.py:16:def main() -> int:
tests/test_spatial_experiment.py:19:def test_common_continuous_gaussian_sampler_is_bounded_and_reproducible():
tests/test_spatial_experiment.py:35:def test_spatial_predeclaration_has_constant_ratio_and_one_common_grid():
tests/test_spatial_experiment.py:58:def test_full_spd_predeclarations_reconstruct_diffusion_and_fix_reference_seed():
tests/test_spatial_experiment.py:77:def test_mature_bimodal_predeclaration_is_full_spd_and_common_grid():
tests/test_spatial_experiment.py:95:def test_fine_graded_predeclaration_aligns_both_comparators_to_common_grid():
tests/test_spatial_experiment.py:119:def test_time_aggregated_design_is_aligned_and_respects_uniform_cell_ceiling():
tests/test_spatial_experiment.py:135:def test_z_conditioning_and_truncated_mixture_sampling_preserve_lobe_symmetry():
operator_learning/numerics.py:6:def conservative_coarsen(density, shape):
operator_learning/numerics.py:17:def density_l1(a, b, voxel_volume):
operator_learning/numerics.py:26:def normalized_probability(density):
operator_learning/numerics.py:33:def boundary_mass(probability, layers):
operator_learning/numerics.py:40:def nearest_target(training_inputs, training_targets, query, voxel_volume):
operator_learning/numerics.py:47:def group_split(groups, seed, counts):
lorenz_fpe/local_projection.py:34:class CellProjectionResult:
lorenz_fpe/local_projection.py:46:class LocalPolynomialProjector:
lorenz_fpe/local_projection.py:55:    def __init__(
lorenz_fpe/local_projection.py:131:    def _objective(self, candidate: np.ndarray, raw: np.ndarray) -> float:
lorenz_fpe/local_projection.py:135:    def _scaling_candidate(self, normalized: np.ndarray) -> np.ndarray:
lorenz_fpe/local_projection.py:143:    def project_cell(
lorenz_fpe/local_projection.py:266:    def scaling_fallback(
lorenz_fpe/local_projection.py:281:    def project_state(
lorenz_fpe/local_projection.py:476:class LocalProjectionFokkerPlanckSolver(FokkerPlanckSolver):
lorenz_fpe/local_projection.py:479:    def __init__(self, *args, **kwargs) -> None:
lorenz_fpe/local_projection.py:498:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/local_projection.py:519:    def local_projection_history_summary(self) -> dict[str, object]:
tests/test_solver_smoke.py:7:class TestSolverSmoke(unittest.TestCase):
tests/test_solver_smoke.py:9:    def setUpClass(cls):
tests/test_solver_smoke.py:11:    def test_forecast_probability_invariants(self):
tests/test_solver_smoke.py:22:    def test_structured_roundtrip_conserves_mass(self):
tests/test_solver_smoke.py:26:    def test_forecast_ksp_tolerances_are_configurable(self):
tests/test_solver_smoke.py:34:    def test_graded_hex_common_grid_export_is_conservative(self):
tests/test_solver_smoke.py:51:    def test_refined_structured_roundtrip_preserves_q1_shape(self):
tests/test_solver_smoke.py:59:    def test_checkpoint_and_da_continuity_without_gaussianisation(self):
scripts/train_neural_pilot.py:13:class Spectral(nn.Module):
scripts/train_neural_pilot.py:14:    def __init__(self, width=8, modes=4):
scripts/train_neural_pilot.py:19:    def forward(self, x):
scripts/train_neural_pilot.py:28:class Operator(nn.Module):
scripts/train_neural_pilot.py:29:    def __init__(self):
scripts/train_neural_pilot.py:38:    def forward(self, density):
scripts/train_neural_pilot.py:52:def metrics(prediction, target):
scripts/train_neural_pilot.py:55:    def statistics(field):
scripts/train_neural_pilot.py:67:def main(root):
lorenz_fpe/finite_volume.py:21:class FiniteVolumeResult:
lorenz_fpe/finite_volume.py:30:class ConservativeFiniteVolume:
lorenz_fpe/finite_volume.py:38:    def __init__(self, model: Lorenz63Model, domain: Domain, cfl: float = 0.72):
lorenz_fpe/finite_volume.py:64:    def _build_face_velocities(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/finite_volume.py:70:        def component(a, b, c, index):
lorenz_fpe/finite_volume.py:78:    def rhs(self, density: np.ndarray) -> np.ndarray:
lorenz_fpe/finite_volume.py:100:    def propagate(self, density: np.ndarray, t0: float, t1: float) -> FiniteVolumeResult:
lorenz_fpe/finite_volume.py:126:    def diagnostics(self, density: np.ndarray) -> dict[str, object]:
operator_learning/governance.py:25:def render_state(state):
operator_learning/governance.py:32:def render_gates(gates):
operator_learning/governance.py:46:def validate_programme(state, gates, generators):
operator_learning/governance.py:114:def validate_predeclaration(config):
operator_learning/governance.py:135:def validate_provenance(record):
operator_learning/governance.py:154:def check_repository(root):
tests/test_neural_pilot_export.py:9:def test_aligned_coarsening_preserves_mass():
tests/test_neural_pilot_export.py:26:def test_sampled_prior_is_positive_normalized_and_reproducible():
tests/test_neural_pilot_export.py:47:def test_full_first_attractor_cloud_has_no_negative_smoothing_tails():
lorenz_fpe/dataset.py:16:class DatasetConfig:
lorenz_fpe/dataset.py:30:class DatasetSplitter:
lorenz_fpe/dataset.py:32:    def split(trajectory_ids: list[str], seed: int = 1729) -> dict[str,list[str]]:
lorenz_fpe/dataset.py:40:class DatasetGenerator:
lorenz_fpe/dataset.py:41:    def __init__(self, solver: FokkerPlanckSolver, config: DatasetConfig):
lorenz_fpe/dataset.py:44:    def generate(self, root: Path) -> dict[str,object]:
lorenz_fpe/dataset.py:131:    def _mode_count(a: np.ndarray, relative_threshold: float = 0.05) -> int:
lorenz_fpe/dataset.py:148:    def _distribution_report(rows: list[dict[str,object]]) -> dict[str,object]:
scripts/run_experiment.py:22:def matched_marginal_tvs(
scripts/run_experiment.py:45:def package_version(name: str) -> str | None:
scripts/run_experiment.py:52:def git_text(*args: str) -> str:
scripts/run_experiment.py:58:def main(config_path: Path, resume_run_dir: Path | None = None) -> int:
tests/test_mpi_consistency.py:4:class TestMPIConsistency(unittest.TestCase):
tests/test_mpi_consistency.py:5:    def _run(self,ranks):
tests/test_mpi_consistency.py:13:    def test_two_rank_limiter_agrees_with_serial(self):
tests/test_limiter.py:6:class TestProjection(unittest.TestCase):
tests/test_limiter.py:7:    def test_positive_and_conservative(self):
tests/test_limiter.py:12:    def test_identity(self):
tests/test_limiter.py:14:    def test_roundoff_repair_cannot_create_negative_active_entries(self):
tests/test_limiter.py:22:    def test_trajectory_split_is_disjoint(self):
lorenz_fpe/core.py:34:def _global_sum(comm: MPI.Comm, value: float) -> float:
lorenz_fpe/core.py:38:def _global_min(comm: MPI.Comm, value: float) -> float:
lorenz_fpe/core.py:42:def _global_max(comm: MPI.Comm, value: float) -> float:
lorenz_fpe/core.py:47:class Domain:
lorenz_fpe/core.py:54:    def volume(self) -> float:
lorenz_fpe/core.py:59:class Lorenz63Model:
lorenz_fpe/core.py:68:    def diffusion(self) -> np.ndarray:
lorenz_fpe/core.py:72:    def drift_numpy(self, x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:79:    def drift_ufl(self, x: ufl.core.expr.Expr) -> ufl.core.expr.Expr:
lorenz_fpe/core.py:88:class DensityState:
lorenz_fpe/core.py:93:    def copy(self, label: str | None = None) -> "DensityState":
lorenz_fpe/core.py:99:    def save_native(self, path: Path) -> None:
lorenz_fpe/core.py:109:class LimiterReport:
lorenz_fpe/core.py:150:class PositivityLimiter:
lorenz_fpe/core.py:165:    def __init__(self, V: fem.FunctionSpace, cell_volumes: np.ndarray,
lorenz_fpe/core.py:202:        def bernstein_1d(i,t):
lorenz_fpe/core.py:225:    def _split_bernstein_axis(values: np.ndarray, axis: int) -> tuple[np.ndarray,np.ndarray]:
lorenz_fpe/core.py:238:    def _split_bernstein_box(cls, values: np.ndarray) -> list[np.ndarray]:
lorenz_fpe/core.py:244:    def classify_coefficients(self, coefficients: np.ndarray,
lorenz_fpe/core.py:287:    def _classification_summary(self, coefficients: np.ndarray) -> dict[str,object]:
lorenz_fpe/core.py:310:    def classification_records(self, coefficients: np.ndarray) -> list[dict[str,object]]:
lorenz_fpe/core.py:328:    def cell_average(self, coefficients: np.ndarray) -> float:
lorenz_fpe/core.py:331:    def control_coefficients(self, coefficients: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:334:    def subcell_average_matrix(self, subdivisions: int) -> np.ndarray:
lorenz_fpe/core.py:339:    def subcell_average_matrix_anisotropic(
lorenz_fpe/core.py:360:    def _difference_norms(self, before: np.ndarray, after: np.ndarray) -> tuple[float,float]:
lorenz_fpe/core.py:372:    def project_cell_averages(w: np.ndarray, volumes: np.ndarray, lower: float = 0.0) -> np.ndarray:
lorenz_fpe/core.py:423:    def apply(self, state: DensityState) -> LimiterReport:
lorenz_fpe/core.py:564:class FokkerPlanckSolver:
lorenz_fpe/core.py:567:    def __init__(
lorenz_fpe/core.py:707:    def _cell_volumes(self) -> np.ndarray:
lorenz_fpe/core.py:714:    def _integral(self, expr: ufl.core.expr.Expr, quadrature_degree: int | None = None) -> float:
lorenz_fpe/core.py:720:    def gaussian_expression(self, mean: Iterable[float], covariance: np.ndarray):
lorenz_fpe/core.py:730:    def project_expression(
lorenz_fpe/core.py:772:    def gaussian_interpolated(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:780:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:790:    def gaussian_projected(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:799:    def gaussian(self, mean: Iterable[float], covariance: np.ndarray, label: str = "gaussian") -> DensityState:
lorenz_fpe/core.py:807:    def sample_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:855:    def sample_q1_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:862:    def load_native(self, path: Path) -> DensityState:
lorenz_fpe/core.py:874:    def from_structured(self, density: np.ndarray, time_value: float = 0.0,
lorenz_fpe/core.py:918:    def mixture(self, means: list[Iterable[float]], covariances: list[np.ndarray], weights: Iterable[float]) -> DensityState:
lorenz_fpe/core.py:925:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:935:    def normalize(self, state: DensityState) -> float:
lorenz_fpe/core.py:943:    def mass(self, state: DensityState) -> float:
lorenz_fpe/core.py:946:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/core.py:985:    def limiter_stage_states(self, time_value: float) -> dict[str,DensityState]:
lorenz_fpe/core.py:997:    def limiter_history_summary(self) -> dict[str,object]:
lorenz_fpe/core.py:1025:    def forecast(self, posterior: DensityState, t0: float, t1: float, progress: bool = False) -> DensityState:
lorenz_fpe/core.py:1050:    def cell_averages(self, state: DensityState) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/core.py:1059:    def structured_export(self, state: DensityState, subcells_per_cell: int = 1) -> np.ndarray:
lorenz_fpe/core.py:1089:    def common_grid_export(
lorenz_fpe/core.py:1139:    def diagnostics(self, state: DensityState) -> dict[str, object]:
lorenz_fpe/core.py:1185:class ObservationModel:
lorenz_fpe/core.py:1191:    def named(cls, name: str, variance: float = 4.0) -> "ObservationModel":
lorenz_fpe/core.py:1200:    def observe(self, state: np.ndarray, rng: np.random.Generator) -> np.ndarray:
lorenz_fpe/core.py:1205:class BayesianAnalysis:
lorenz_fpe/core.py:1206:    def __init__(self, solver: FokkerPlanckSolver, observation_model: ObservationModel,
lorenz_fpe/core.py:1238:    def update(self, forecast: DensityState, observation: np.ndarray) -> tuple[DensityState, dict[str,object]]:
lorenz_fpe/core.py:1278:class TruthSimulator:
lorenz_fpe/core.py:1279:    def __init__(self, model: Lorenz63Model, dt: float = 2.5e-4):
lorenz_fpe/core.py:1282:    def simulate(self, initial: Iterable[float], times: Iterable[float], seed: int) -> np.ndarray:
lorenz_fpe/core.py:1293:def solver_metadata(solver: FokkerPlanckSolver) -> dict[str, object]:
lorenz_fpe/core.py:1328:def write_json(path: Path, obj: object) -> None:
tests/test_mfem_mature_compare.py:8:def test_uniform_voxel_statistics() -> None:
tests/test_accuracy_repairs.py:23:class TestProjectionAndSamplingAccuracy(unittest.TestCase):
tests/test_accuracy_repairs.py:24:    def test_l2_projection_preserves_mass_and_improves_gaussian_covariance(self):
tests/test_accuracy_repairs.py:46:    def test_limited_projection_is_positive_and_mass_conservative(self):
tests/test_accuracy_repairs.py:59:    def test_native_q1_sampler_recovers_linear_density_mean(self):
tests/test_accuracy_repairs.py:73:class TestAnalysisAndBoundaryAccuracy(unittest.TestCase):
tests/test_accuracy_repairs.py:74:    def test_projected_bayes_update_is_normalized_and_improves_covariance(self):
tests/test_accuracy_repairs.py:88:    def test_total_flux_manufactured_solution_converges(self):
tests/test_accuracy_repairs.py:98:class TestQ2Properties(unittest.TestCase):
tests/test_accuracy_repairs.py:99:    def test_q2_projection_preserves_second_moments_before_limiting(self):
tests/test_accuracy_repairs.py:116:    def test_q2_bernstein_limiter_and_voxel_roundtrip(self):
tests/test_accuracy_repairs.py:136:    def test_adaptive_bernstein_classification_distinguishes_three_outcomes(self):
tests/test_accuracy_repairs.py:143:        def classify(offset):
tests/test_accuracy_repairs.py:171:    def test_q2_limiter_scaling_factors_stay_in_unit_interval(self):
tests/test_accuracy_repairs.py:186:    def test_forecast_can_record_an_unlimited_q2_trajectory(self):
tests/test_accuracy_repairs.py:202:    def test_structured_q1_embedding_into_q2_is_exact(self):
tests/test_accuracy_repairs.py:212:    def test_local_q2_projection_is_conservative_positive_and_minimum_change(self):
tests/test_accuracy_repairs.py:237:    def test_osqp_local_projection_agrees_with_slsqp_oracle(self):
tests/test_accuracy_repairs.py:269:    def test_local_projection_reports_optimizer_fallback_and_true_iteration_mean(self):
tests/test_accuracy_repairs.py:286:        def fail_projection(coefficients, **kwargs):
tests/test_accuracy_repairs.py:319:    def test_local_projection_retains_actual_stage1_state(self):
tests/test_accuracy_repairs.py:361:    def test_local_q2_projection_exposes_negative_average_infeasibility(self):
tests/test_accuracy_repairs.py:373:    def test_local_q2_projection_honours_prescribed_zero_average(self):
tests/test_accuracy_repairs.py:387:    def test_local_projection_solver_feeds_certified_state_forward(self):
tests/test_accuracy_repairs.py:413:class TestIndependentFiniteVolume(unittest.TestCase):
tests/test_accuracy_repairs.py:414:    def test_total_flux_update_preserves_mass_and_positivity(self):
lorenz_fpe/afc.py:26:class AFCProjectionFokkerPlanckSolver(FokkerPlanckSolver):
lorenz_fpe/afc.py:29:    def __init__(self, *args, **kwargs) -> None:
lorenz_fpe/afc.py:51:    def _prepare_structured_layout(self) -> None:
lorenz_fpe/afc.py:75:    def _paired_slices(shape: tuple[int, int, int], shift: tuple[int, int, int]):
lorenz_fpe/afc.py:90:    def _prepare_low_order_operator(self) -> None:
lorenz_fpe/afc.py:165:    def _gather_averages(self, state: DensityState) -> np.ndarray | None:
lorenz_fpe/afc.py:175:    def _scatter_averages(self, values: np.ndarray | None) -> np.ndarray:
lorenz_fpe/afc.py:183:    def _positive_low_order_step(self, old: np.ndarray) -> np.ndarray:
lorenz_fpe/afc.py:197:    def _limited_antidiffusion(low: np.ndarray, high: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
lorenz_fpe/afc.py:227:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/afc.py:300:    def local_projection_history_summary(self) -> dict[str, object]:
scripts/prepare_operator_run.py:17:def git(*args):
scripts/prepare_operator_run.py:21:def prepare(source):
tests/test_memory_backpressure.py:12:def test_pause_resume_hysteresis_without_termination():
tests/test_memory_backpressure.py:13:    class Process:
tests/test_memory_backpressure.py:17:        def poll(self):
tests/test_memory_backpressure.py:31:def test_resume_at_exact_two_gib_preserves_process():
tests/test_memory_backpressure.py:32:    class Process:
tests/test_memory_backpressure.py:36:        def poll(self):
scripts/plot_saved_density.py:21:def render(p, edges, title, time):
scripts/plot_saved_density.py:51:def main():
scripts/package_solver_monograph.py:15:def digest(path):
scripts/package_solver_monograph.py:19:def main():
scripts/build_solver_monograph_evidence.py:17:def tex(s):
scripts/build_solver_monograph_evidence.py:21:def flatten(obj, prefix=''):
scripts/build_solver_monograph_evidence.py:34:def main():
scripts/build_solver_monograph_evidence.py:134:def render_appendices(ledger):
scripts/audit_operator_pilot.py:17:def sha(path):
scripts/audit_operator_pilot.py:21:def audit(source, output):
scripts/audit_operator_pilot.py:81:            def means(field):
tests/operator_learning/test_numerics.py:10:def test_conservative_export_and_l1():
tests/operator_learning/test_numerics.py:19:def test_probability_and_boundary():
tests/operator_learning/test_numerics.py:29:def test_nearest_baseline_only_uses_training_targets():
tests/operator_learning/test_numerics.py:37:def test_group_split_reproducible_no_window_leakage():
scripts/check_neural_pilot_gpu.py:10:def main():
tests/operator_learning/test_historical_evidence.py:9:def report():
tests/operator_learning/test_historical_evidence.py:17:def test_historical_operational_acceptance_and_provenance():
tests/operator_learning/test_historical_evidence.py:33:def test_pilot_errors_preserved_without_qualification():
tests/operator_learning/test_model_optional.py:8:def test_historical_model_forward_backward():
tests/operator_learning/test_governance.py:14:def programme():
tests/operator_learning/test_governance.py:20:def test_canonical_repository():
tests/operator_learning/test_governance.py:24:def test_wrong_next_gate_rejected():
tests/operator_learning/test_governance.py:30:def test_locked_gate_cannot_be_opened_before_alignment():
tests/operator_learning/test_governance.py:40:def test_no_premature_authorization(field):
tests/operator_learning/test_governance.py:46:def test_pass_requires_adjudication_and_thresholds():
tests/operator_learning/test_governance.py:55:def test_unverified_generator_has_no_training_permission():
tests/operator_learning/test_governance.py:61:def test_draft_config_cannot_prepare():
tests/operator_learning/test_governance.py:67:def test_provenance_rejects_missing_or_invalid_hashes():
tests/operator_learning/test_legacy_contract.py:12:def legacy():
tests/operator_learning/test_legacy_contract.py:27:def test_unsupported_legacy_config_rejected(field, value):
tests/operator_learning/test_legacy_contract.py:37:def test_historical_relaunch_blocked_by_default(monkeypatch):
