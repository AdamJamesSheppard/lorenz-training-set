# Repository map

Generated: 2026-09-11T18:32:56+01:00

```text
docs/ACTIVE_TASK.md
docs/ARCHITECTURE.md
docs/CLAIMS.md
docs/DECISIONS.md
docs/MATHEMATICAL_SPEC.md
docs/MATH_PROTOCOL.md
docs/PROJECT_STATE.md
docs/REFERENCES.md
docs/RESEARCH_DIRECTIONS.md
docs/assumptions.yaml
docs/generated/REPO_MAP.md
docs/tasks/TASK_TEMPLATE.md
experiments/corrected-q2-crank-nicolson.yaml
experiments/local-q2-crank-nicolson.yaml
experiments/local-q2-optimizer-validation.yaml
experiments/local-q2-osqp-profile.yaml
experiments/local-q2-positivity-projection.yaml
experiments/mature-state-decision.yaml
experiments/method-selection-research.yaml
experiments/same-mesh-q2-corrected.yaml
experiments/same-mesh-q2-falsification.yaml
experiments/same-mesh-q2-timestep.yaml
experiments/smoke-forecast.yaml
experiments/unlimited-q2-crank-nicolson.yaml
experiments/unlimited-q2-timestep-attribution.yaml
lorenz_fpe/__init__.py
lorenz_fpe/core.py
lorenz_fpe/dataset.py
lorenz_fpe/finite_volume.py
lorenz_fpe/local_projection.py
lorenz_fpe/validation.py
scripts/bootstrap
scripts/check
scripts/context
scripts/repo-map
scripts/run-experiment
scripts/run-in-env
scripts/run_experiment.py
scripts/verify-math
scripts/verify_math.py
tests/__init__.py
tests/mpi_probe_worker.py
tests/test_accuracy_repairs.py
tests/test_limiter.py
tests/test_mpi_consistency.py
tests/test_solver_smoke.py
tests/test_validation.py
./AGENTS.md
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
./local_q2_optimizer_validation_report.json
./local_q2_positivity_projection_report.json
./local_q2_projection_performance_report.json
./mature_da_projected_report.json
./mature_da_report.json
./mature_da_study.py
./mature_forecast_validation.json
./mature_forecast_validation.py
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
./same_mesh_q2_study.py:29:def _sha256(path: Path) -> str:
./same_mesh_q2_study.py:37:def _marginal_tv(cell_averages: np.ndarray, particles: np.ndarray,
./same_mesh_q2_study.py:49:def prepare_reference(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:84:def run_forecast(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:247:def recover_final(args: argparse.Namespace) -> None:
./same_mesh_q2_study.py:286:def parser() -> argparse.ArgumentParser:
./build_experiment_manifest.py:52:def sha256(path: Path) -> str:
./build_experiment_manifest.py:60:def git_revision() -> str | None:
./build_experiment_manifest.py:70:def extract_configuration(path: Path) -> dict[str, object]:
./build_experiment_manifest.py:79:def command_output(command: list[str]) -> str | None:
./build_experiment_manifest.py:86:def main() -> None:
./local_projection_optimizer_study.py:18:def _sha256(path: Path) -> str:
./local_projection_optimizer_study.py:26:def _terminal_problems(
./local_projection_optimizer_study.py:48:def _random_problems(
./local_projection_optimizer_study.py:61:def run(args: argparse.Namespace) -> None:
./local_projection_optimizer_study.py:200:def parser() -> argparse.ArgumentParser:
./local_projection_study.py:21:def _sha256(path: Path) -> str:
./local_projection_study.py:29:def _marginal_tv(
./local_projection_study.py:44:def _difference_report(
./local_projection_study.py:66:def run(args: argparse.Namespace) -> None:
./local_projection_study.py:204:def parser() -> argparse.ArgumentParser:
./mature_da_study.py:11:def tensor_stats(a,domain):
./mature_da_study.py:28:def main():
./mature_forecast_validation.py:11:def sample_q1(solver,state,n,rng):
./mature_forecast_validation.py:23:def main():
scripts/verify_math.py:16:def main() -> int:
tests/test_validation.py:4:class TestAnalyticBenchmarks(unittest.TestCase):
tests/test_validation.py:6:    def setUpClass(cls):
tests/test_validation.py:8:    def test_pure_diffusion(self):
tests/test_validation.py:12:    def test_constant_advection_diffusion(self):
tests/test_validation.py:16:    def test_non_gaussian(self):
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
tests/test_solver_smoke.py:7:class TestSolverSmoke(unittest.TestCase):
tests/test_solver_smoke.py:9:    def setUpClass(cls):
tests/test_solver_smoke.py:11:    def test_forecast_probability_invariants(self):
tests/test_solver_smoke.py:22:    def test_structured_roundtrip_conserves_mass(self):
tests/test_solver_smoke.py:26:    def test_refined_structured_roundtrip_preserves_q1_shape(self):
tests/test_solver_smoke.py:34:    def test_checkpoint_and_da_continuity_without_gaussianisation(self):
scripts/run_experiment.py:22:def package_version(name: str) -> str | None:
scripts/run_experiment.py:29:def git_text(*args: str) -> str:
scripts/run_experiment.py:35:def main(config_path: Path) -> int:
lorenz_fpe/local_projection.py:34:class CellProjectionResult:
lorenz_fpe/local_projection.py:46:class LocalPolynomialProjector:
lorenz_fpe/local_projection.py:55:    def __init__(
lorenz_fpe/local_projection.py:130:    def _objective(self, candidate: np.ndarray, raw: np.ndarray) -> float:
lorenz_fpe/local_projection.py:134:    def _scaling_candidate(self, normalized: np.ndarray) -> np.ndarray:
lorenz_fpe/local_projection.py:142:    def project_cell(
lorenz_fpe/local_projection.py:265:    def scaling_fallback(
lorenz_fpe/local_projection.py:280:    def project_state(
lorenz_fpe/local_projection.py:468:class LocalProjectionFokkerPlanckSolver(FokkerPlanckSolver):
lorenz_fpe/local_projection.py:471:    def __init__(self, *args, **kwargs) -> None:
lorenz_fpe/local_projection.py:490:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/local_projection.py:511:    def local_projection_history_summary(self) -> dict[str, object]:
tests/test_mpi_consistency.py:4:class TestMPIConsistency(unittest.TestCase):
tests/test_mpi_consistency.py:5:    def _run(self,ranks):
tests/test_mpi_consistency.py:13:    def test_two_rank_limiter_agrees_with_serial(self):
lorenz_fpe/finite_volume.py:21:class FiniteVolumeResult:
lorenz_fpe/finite_volume.py:30:class ConservativeFiniteVolume:
lorenz_fpe/finite_volume.py:38:    def __init__(self, model: Lorenz63Model, domain: Domain, cfl: float = 0.72):
lorenz_fpe/finite_volume.py:64:    def _build_face_velocities(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/finite_volume.py:70:        def component(a, b, c, index):
lorenz_fpe/finite_volume.py:78:    def rhs(self, density: np.ndarray) -> np.ndarray:
lorenz_fpe/finite_volume.py:100:    def propagate(self, density: np.ndarray, t0: float, t1: float) -> FiniteVolumeResult:
lorenz_fpe/finite_volume.py:126:    def diagnostics(self, density: np.ndarray) -> dict[str, object]:
tests/test_limiter.py:6:class TestProjection(unittest.TestCase):
tests/test_limiter.py:7:    def test_positive_and_conservative(self):
tests/test_limiter.py:12:    def test_identity(self):
tests/test_limiter.py:14:    def test_roundoff_repair_cannot_create_negative_active_entries(self):
tests/test_limiter.py:22:    def test_trajectory_split_is_disjoint(self):
lorenz_fpe/dataset.py:16:class DatasetConfig:
lorenz_fpe/dataset.py:30:class DatasetSplitter:
lorenz_fpe/dataset.py:32:    def split(trajectory_ids: list[str], seed: int = 1729) -> dict[str,list[str]]:
lorenz_fpe/dataset.py:40:class DatasetGenerator:
lorenz_fpe/dataset.py:41:    def __init__(self, solver: FokkerPlanckSolver, config: DatasetConfig):
lorenz_fpe/dataset.py:44:    def generate(self, root: Path) -> dict[str,object]:
lorenz_fpe/dataset.py:131:    def _mode_count(a: np.ndarray, relative_threshold: float = 0.05) -> int:
lorenz_fpe/dataset.py:148:    def _distribution_report(rows: list[dict[str,object]]) -> dict[str,object]:
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
tests/test_accuracy_repairs.py:316:    def test_local_projection_retains_actual_stage1_state(self):
tests/test_accuracy_repairs.py:358:    def test_local_q2_projection_exposes_negative_average_infeasibility(self):
tests/test_accuracy_repairs.py:370:    def test_local_q2_projection_honours_prescribed_zero_average(self):
tests/test_accuracy_repairs.py:384:    def test_local_projection_solver_feeds_certified_state_forward(self):
tests/test_accuracy_repairs.py:410:class TestIndependentFiniteVolume(unittest.TestCase):
tests/test_accuracy_repairs.py:411:    def test_total_flux_update_preserves_mass_and_positivity(self):
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
lorenz_fpe/core.py:349:    def _difference_norms(self, before: np.ndarray, after: np.ndarray) -> tuple[float,float]:
lorenz_fpe/core.py:361:    def project_cell_averages(w: np.ndarray, volumes: np.ndarray, lower: float = 0.0) -> np.ndarray:
lorenz_fpe/core.py:412:    def apply(self, state: DensityState) -> LimiterReport:
lorenz_fpe/core.py:553:class FokkerPlanckSolver:
lorenz_fpe/core.py:556:    def __init__(
lorenz_fpe/core.py:651:    def _cell_volumes(self) -> np.ndarray:
lorenz_fpe/core.py:658:    def _integral(self, expr: ufl.core.expr.Expr, quadrature_degree: int | None = None) -> float:
lorenz_fpe/core.py:664:    def gaussian_expression(self, mean: Iterable[float], covariance: np.ndarray):
lorenz_fpe/core.py:674:    def project_expression(
lorenz_fpe/core.py:716:    def gaussian_interpolated(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:724:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:734:    def gaussian_projected(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:743:    def gaussian(self, mean: Iterable[float], covariance: np.ndarray, label: str = "gaussian") -> DensityState:
lorenz_fpe/core.py:751:    def sample_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:799:    def sample_q1_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:806:    def load_native(self, path: Path) -> DensityState:
lorenz_fpe/core.py:818:    def from_structured(self, density: np.ndarray, time_value: float = 0.0,
lorenz_fpe/core.py:862:    def mixture(self, means: list[Iterable[float]], covariances: list[np.ndarray], weights: Iterable[float]) -> DensityState:
lorenz_fpe/core.py:869:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:879:    def normalize(self, state: DensityState) -> float:
lorenz_fpe/core.py:887:    def mass(self, state: DensityState) -> float:
lorenz_fpe/core.py:890:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/core.py:929:    def limiter_stage_states(self, time_value: float) -> dict[str,DensityState]:
lorenz_fpe/core.py:941:    def limiter_history_summary(self) -> dict[str,object]:
lorenz_fpe/core.py:969:    def forecast(self, posterior: DensityState, t0: float, t1: float, progress: bool = False) -> DensityState:
lorenz_fpe/core.py:994:    def cell_averages(self, state: DensityState) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/core.py:1003:    def structured_export(self, state: DensityState, subcells_per_cell: int = 1) -> np.ndarray:
lorenz_fpe/core.py:1031:    def diagnostics(self, state: DensityState) -> dict[str, object]:
lorenz_fpe/core.py:1077:class ObservationModel:
lorenz_fpe/core.py:1083:    def named(cls, name: str, variance: float = 4.0) -> "ObservationModel":
lorenz_fpe/core.py:1092:    def observe(self, state: np.ndarray, rng: np.random.Generator) -> np.ndarray:
lorenz_fpe/core.py:1097:class BayesianAnalysis:
lorenz_fpe/core.py:1098:    def __init__(self, solver: FokkerPlanckSolver, observation_model: ObservationModel,
lorenz_fpe/core.py:1130:    def update(self, forecast: DensityState, observation: np.ndarray) -> tuple[DensityState, dict[str,object]]:
lorenz_fpe/core.py:1170:class TruthSimulator:
lorenz_fpe/core.py:1171:    def __init__(self, model: Lorenz63Model, dt: float = 2.5e-4):
lorenz_fpe/core.py:1174:    def simulate(self, initial: Iterable[float], times: Iterable[float], seed: int) -> np.ndarray:
lorenz_fpe/core.py:1185:def solver_metadata(solver: FokkerPlanckSolver) -> dict[str, object]:
lorenz_fpe/core.py:1217:def write_json(path: Path, obj: object) -> None:
