"""Accuracy/regression tests for the repaired validation operators.

These are intentionally separate from the inexpensive smoke tests.  They
check mathematical properties that were central to the method-selection
study rather than merely checking that a solve completes.
"""

import unittest

import numpy as np
from dolfinx import fem

from lorenz_fpe import Domain, FokkerPlanckSolver, Lorenz63Model
from lorenz_fpe.finite_volume import ConservativeFiniteVolume
from lorenz_fpe.validation import ConstantModel
from lorenz_fpe.validation import (
    analytic_bayesian_update_study,
    gaussian_representation_metrics,
    manufactured_total_flux_boundary,
)


class TestProjectionAndSamplingAccuracy(unittest.TestCase):
    def test_l2_projection_preserves_mass_and_improves_gaussian_covariance(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(cells=(8, 10, 10)), 0.00125
        )
        mean = (1.0, 1.0, 20.0)
        covariance = np.diag([4.0, 4.0, 9.0])
        interpolated = solver.gaussian_interpolated(mean, covariance)
        interpolation = gaussian_representation_metrics(
            solver, interpolated, mean, covariance, 14
        )
        projected = solver.gaussian_projected(
            mean, covariance, quadrature_degree=14, apply_limiter=False
        )
        projection = gaussian_representation_metrics(
            solver, projected, mean, covariance, 14
        )
        self.assertLess(abs(projection["mass"] - 1.0), 1.0e-11)
        self.assertLess(
            projection["normalized_covariance_error"],
            0.25 * interpolation["normalized_covariance_error"],
        )

    def test_limited_projection_is_positive_and_mass_conservative(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(cells=(8, 10, 10)), 0.00125
        )
        state = solver.gaussian_projected(
            (1.0, 1.0, 20.0), np.diag([4.0, 4.0, 9.0]),
            quadrature_degree=14, apply_limiter=True,
        )
        report = solver.last_initialization_report["limiter"]
        self.assertLess(abs(solver.mass(state) - 1.0), 1.0e-11)
        self.assertGreaterEqual(report["minimum_after"], -1.0e-13)
        self.assertLess(abs(report["mass_before"] - report["mass_after"]), 1.0e-11)

    def test_native_q1_sampler_recovers_linear_density_mean(self):
        domain = Domain(((-1.0, 1.0),) * 3, (2, 2, 2))
        solver = FokkerPlanckSolver(Lorenz63Model(), domain, 0.01)
        q = fem.Function(solver.V)
        q.interpolate(lambda x: (1.0 + 0.4 * x[0]) / 8.0)
        from lorenz_fpe.core import DensityState
        state = DensityState(q, 0.0, "linear_test_density")
        solver.limiter.apply(state)
        samples = solver.sample_density(state, 20000, np.random.default_rng(9071))
        self.assertLess(abs(samples[:, 0].mean() - 0.4 / 3.0), 0.02)
        self.assertLess(abs(samples[:, 1].mean()), 0.02)
        self.assertLess(abs(samples[:, 2].mean()), 0.02)


class TestAnalysisAndBoundaryAccuracy(unittest.TestCase):
    def test_projected_bayes_update_is_normalized_and_improves_covariance(self):
        report = analytic_bayesian_update_study(
            resolutions=((8, 10, 10),), quadrature_degree=14
        )
        rows = {row["method"]: row for row in report["rows"]}
        nodal = rows["nodal"]["posterior"]
        projected = rows["projected"]["posterior"]
        self.assertLess(abs(projected["mass"] - 1.0), 1.0e-11)
        self.assertGreaterEqual(projected["minimum"], -1.0e-13)
        self.assertLess(
            projected["normalized_covariance_error"],
            nodal["normalized_covariance_error"],
        )

    def test_total_flux_manufactured_solution_converges(self):
        report = manufactured_total_flux_boundary(
            resolutions=(3, 4, 6), dt=0.0005, t_final=0.003
        )
        rows = report["rows"]
        self.assertLess(rows[-1]["l1_error"], rows[-2]["l1_error"])
        self.assertGreater(rows[-1]["observed_l1_order"], 1.7)
        self.assertLess(rows[-1]["mass_error"], 1.0e-10)


class TestQ2Properties(unittest.TestCase):
    def test_q2_projection_preserves_second_moments_before_limiting(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(cells=(6, 8, 8)), 0.0025, degree=2
        )
        mean = (1.0, 1.0, 20.0)
        covariance = np.array(
            [[4.0, 0.8, 0.3], [0.8, 5.0, -0.4], [0.3, -0.4, 9.0]]
        )
        state = solver.gaussian_projected(
            mean, covariance, quadrature_degree=20, apply_limiter=False
        )
        metrics = gaussian_representation_metrics(
            solver, state, mean, covariance, quadrature_degree=22
        )
        self.assertLess(np.linalg.norm(metrics["mean_error"]), 1.0e-7)
        self.assertLess(metrics["normalized_covariance_error"], 1.0e-6)

    def test_q2_bernstein_limiter_and_voxel_roundtrip(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(((-3.0, 3.0),) * 3, (2, 2, 2)),
            0.01, degree=2
        )
        state = solver.gaussian_projected(
            (0.0, 0.0, 0.0), np.diag([0.4, 0.6, 0.8]),
            quadrature_degree=14, apply_limiter=True,
        )
        for cell in range(solver.mesh.topology.index_map(3).size_local):
            coefficients = state.function.x.array[solver.V.dofmap.cell_dofs(cell)]
            self.assertGreaterEqual(
                solver.limiter.control_coefficients(coefficients).min(), -1.0e-13
            )
        tensor = solver.structured_export(state, 3)
        restored = solver.from_structured(tensor)
        error = solver._integral(abs(state.function - restored.function), 10)
        self.assertLess(error, 1.0e-10)
        self.assertLess(abs(solver.mass(restored) - 1.0), 1.0e-11)


class TestIndependentFiniteVolume(unittest.TestCase):
    def test_total_flux_update_preserves_mass_and_positivity(self):
        domain = Domain(((-2.0, 2.0),) * 3, (10, 10, 10))
        method = ConservativeFiniteVolume(ConstantModel((0.3, -0.2, 0.1)), domain)
        X = np.meshgrid(*method.centres, indexing="ij")
        density = np.exp(-(X[0] ** 2 + X[1] ** 2 + X[2] ** 2))
        density /= density.sum() * np.prod(method.widths)
        result = method.propagate(density, 0.0, 0.01)
        self.assertLess(abs(result.mass - 1.0), 1.0e-12)
        self.assertGreaterEqual(result.minimum, -1.0e-13)


if __name__ == "__main__":
    unittest.main()
