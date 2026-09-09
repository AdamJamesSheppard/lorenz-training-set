# Repository map

Generated: 2026-09-09T03:37:29+01:00

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
experiments/mature-state-decision.yaml
experiments/method-selection-research.yaml
experiments/smoke-forecast.yaml
lorenz_fpe/__init__.py
lorenz_fpe/core.py
lorenz_fpe/dataset.py
lorenz_fpe/finite_volume.py
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
./crank_nicolson_mc_20x24x24.json
./experiment_manifest.json
./generate_dataset.py
./high_resolution_monte_carlo_report.json
./higher_order_report.json
./independent_reference_refined_report.json
./independent_reference_report.json
./independent_reference_study.py
./limiter_impact_20x24x24.json
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
./validate.py
./validation_repair.py
./validation_repair_report.json
./validation_report.json
./voxel_projection_20x24x24.json
```

## Python symbols
./build_experiment_manifest.py:44:def sha256(path: Path) -> str:
./build_experiment_manifest.py:52:def git_revision() -> str | None:
./build_experiment_manifest.py:62:def extract_configuration(path: Path) -> dict[str, object]:
./build_experiment_manifest.py:71:def command_output(command: list[str]) -> str | None:
./build_experiment_manifest.py:78:def main() -> None:
./mature_da_study.py:11:def tensor_stats(a,domain):
./mature_da_study.py:28:def main():
./mature_forecast_validation.py:11:def sample_q1(solver,state,n,rng):
./mature_forecast_validation.py:23:def main():
scripts/verify_math.py:16:def main() -> int:
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
tests/test_validation.py:4:class TestAnalyticBenchmarks(unittest.TestCase):
tests/test_validation.py:6:    def setUpClass(cls):
tests/test_validation.py:8:    def test_pure_diffusion(self):
tests/test_validation.py:12:    def test_constant_advection_diffusion(self):
tests/test_validation.py:16:    def test_non_gaussian(self):
lorenz_fpe/finite_volume.py:21:class FiniteVolumeResult:
lorenz_fpe/finite_volume.py:30:class ConservativeFiniteVolume:
lorenz_fpe/finite_volume.py:38:    def __init__(self, model: Lorenz63Model, domain: Domain, cfl: float = 0.72):
lorenz_fpe/finite_volume.py:64:    def _build_face_velocities(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/finite_volume.py:70:        def component(a, b, c, index):
lorenz_fpe/finite_volume.py:78:    def rhs(self, density: np.ndarray) -> np.ndarray:
lorenz_fpe/finite_volume.py:100:    def propagate(self, density: np.ndarray, t0: float, t1: float) -> FiniteVolumeResult:
lorenz_fpe/finite_volume.py:126:    def diagnostics(self, density: np.ndarray) -> dict[str, object]:
scripts/run_experiment.py:20:def package_version(name: str) -> str | None:
scripts/run_experiment.py:27:def git_text(*args: str) -> str:
scripts/run_experiment.py:33:def main(config_path: Path) -> int:
tests/test_solver_smoke.py:7:class TestSolverSmoke(unittest.TestCase):
tests/test_solver_smoke.py:9:    def setUpClass(cls):
tests/test_solver_smoke.py:11:    def test_forecast_probability_invariants(self):
tests/test_solver_smoke.py:22:    def test_structured_roundtrip_conserves_mass(self):
tests/test_solver_smoke.py:26:    def test_refined_structured_roundtrip_preserves_q1_shape(self):
tests/test_solver_smoke.py:34:    def test_checkpoint_and_da_continuity_without_gaussianisation(self):
lorenz_fpe/dataset.py:16:class DatasetConfig:
lorenz_fpe/dataset.py:30:class DatasetSplitter:
lorenz_fpe/dataset.py:32:    def split(trajectory_ids: list[str], seed: int = 1729) -> dict[str,list[str]]:
lorenz_fpe/dataset.py:40:class DatasetGenerator:
lorenz_fpe/dataset.py:41:    def __init__(self, solver: FokkerPlanckSolver, config: DatasetConfig):
lorenz_fpe/dataset.py:44:    def generate(self, root: Path) -> dict[str,object]:
lorenz_fpe/dataset.py:131:    def _mode_count(a: np.ndarray, relative_threshold: float = 0.05) -> int:
lorenz_fpe/dataset.py:148:    def _distribution_report(rows: list[dict[str,object]]) -> dict[str,object]:
tests/test_mpi_consistency.py:4:class TestMPIConsistency(unittest.TestCase):
tests/test_mpi_consistency.py:5:    def _run(self,ranks):
tests/test_mpi_consistency.py:13:    def test_two_rank_limiter_agrees_with_serial(self):
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
lorenz_fpe/core.py:138:class PositivityLimiter:
lorenz_fpe/core.py:153:    def __init__(self, V: fem.FunctionSpace, cell_volumes: np.ndarray,
lorenz_fpe/core.py:181:        def bernstein_1d(i,t):
lorenz_fpe/core.py:199:    def cell_average(self, coefficients: np.ndarray) -> float:
lorenz_fpe/core.py:202:    def control_coefficients(self, coefficients: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:205:    def subcell_average_matrix(self, subdivisions: int) -> np.ndarray:
lorenz_fpe/core.py:220:    def _difference_norms(self, before: np.ndarray, after: np.ndarray) -> tuple[float,float]:
lorenz_fpe/core.py:232:    def project_cell_averages(w: np.ndarray, volumes: np.ndarray, lower: float = 0.0) -> np.ndarray:
lorenz_fpe/core.py:262:    def apply(self, state: DensityState) -> LimiterReport:
lorenz_fpe/core.py:369:class FokkerPlanckSolver:
lorenz_fpe/core.py:372:    def __init__(
lorenz_fpe/core.py:459:    def _cell_volumes(self) -> np.ndarray:
lorenz_fpe/core.py:466:    def _integral(self, expr: ufl.core.expr.Expr, quadrature_degree: int | None = None) -> float:
lorenz_fpe/core.py:472:    def gaussian_expression(self, mean: Iterable[float], covariance: np.ndarray):
lorenz_fpe/core.py:482:    def project_expression(
lorenz_fpe/core.py:524:    def gaussian_interpolated(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:532:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:542:    def gaussian_projected(self, mean: Iterable[float], covariance: np.ndarray,
lorenz_fpe/core.py:551:    def gaussian(self, mean: Iterable[float], covariance: np.ndarray, label: str = "gaussian") -> DensityState:
lorenz_fpe/core.py:559:    def sample_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:607:    def sample_q1_density(self, state: DensityState, count: int,
lorenz_fpe/core.py:614:    def load_native(self, path: Path) -> DensityState:
lorenz_fpe/core.py:626:    def from_structured(self, density: np.ndarray, time_value: float = 0.0) -> DensityState:
lorenz_fpe/core.py:668:    def mixture(self, means: list[Iterable[float]], covariances: list[np.ndarray], weights: Iterable[float]) -> DensityState:
lorenz_fpe/core.py:675:        def values(x: np.ndarray) -> np.ndarray:
lorenz_fpe/core.py:685:    def normalize(self, state: DensityState) -> float:
lorenz_fpe/core.py:693:    def mass(self, state: DensityState) -> float:
lorenz_fpe/core.py:696:    def step(self, state: DensityState) -> DensityState:
lorenz_fpe/core.py:729:    def limiter_stage_states(self, time_value: float) -> dict[str,DensityState]:
lorenz_fpe/core.py:741:    def limiter_history_summary(self) -> dict[str,object]:
lorenz_fpe/core.py:753:    def forecast(self, posterior: DensityState, t0: float, t1: float, progress: bool = False) -> DensityState:
lorenz_fpe/core.py:778:    def cell_averages(self, state: DensityState) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
lorenz_fpe/core.py:787:    def structured_export(self, state: DensityState, subcells_per_cell: int = 1) -> np.ndarray:
lorenz_fpe/core.py:815:    def diagnostics(self, state: DensityState) -> dict[str, object]:
lorenz_fpe/core.py:861:class ObservationModel:
lorenz_fpe/core.py:867:    def named(cls, name: str, variance: float = 4.0) -> "ObservationModel":
lorenz_fpe/core.py:876:    def observe(self, state: np.ndarray, rng: np.random.Generator) -> np.ndarray:
lorenz_fpe/core.py:881:class BayesianAnalysis:
lorenz_fpe/core.py:882:    def __init__(self, solver: FokkerPlanckSolver, observation_model: ObservationModel,
lorenz_fpe/core.py:914:    def update(self, forecast: DensityState, observation: np.ndarray) -> tuple[DensityState, dict[str,object]]:
lorenz_fpe/core.py:954:class TruthSimulator:
lorenz_fpe/core.py:955:    def __init__(self, model: Lorenz63Model, dt: float = 2.5e-4):
lorenz_fpe/core.py:958:    def simulate(self, initial: Iterable[float], times: Iterable[float], seed: int) -> np.ndarray:
lorenz_fpe/core.py:969:def solver_metadata(solver: FokkerPlanckSolver) -> dict[str, object]:
lorenz_fpe/core.py:1000:def write_json(path: Path, obj: object) -> None:
tests/test_limiter.py:6:class TestProjection(unittest.TestCase):
tests/test_limiter.py:7:    def test_positive_and_conservative(self):
tests/test_limiter.py:12:    def test_identity(self):
tests/test_limiter.py:14:    def test_trajectory_split_is_disjoint(self):
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
tests/test_accuracy_repairs.py:137:class TestIndependentFiniteVolume(unittest.TestCase):
tests/test_accuracy_repairs.py:138:    def test_total_flux_update_preserves_mass_and_positivity(self):
