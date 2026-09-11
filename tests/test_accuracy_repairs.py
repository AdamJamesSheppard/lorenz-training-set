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

    def test_adaptive_bernstein_classification_distinguishes_three_outcomes(self):
        domain = Domain(((0.0, 1.0),) * 3, (1, 1, 1))
        solver = FokkerPlanckSolver(
            Lorenz63Model(), domain, 0.01, degree=2,
            certificate_mode="adaptive", certificate_max_depth=4,
        )

        def classify(offset):
            q = fem.Function(solver.V)
            q.interpolate(lambda x: (x[0] - 0.37) ** 2 + offset + 0.0 * x[1])
            dofs = solver.V.dofmap.cell_dofs(0)
            return solver.limiter.classify_coefficients(q.x.array[dofs])

        positive = classify(0.002)
        negative = classify(-0.002)
        zero = classify(0.0)
        self.assertEqual(positive["status"], "CERTIFIED_NONNEGATIVE")
        self.assertGreater(positive["depth"], 1)
        self.assertEqual(negative["status"], "WITNESSED_NEGATIVE")
        self.assertLess(negative["witness_value"], 0.0)
        self.assertEqual(zero["status"], "UNRESOLVED")

        q = fem.Function(solver.V)
        q.interpolate(lambda x: (x[0] - 0.37) ** 2 + 0.002 + 0.0 * x[1])
        from lorenz_fpe.core import DensityState
        state = DensityState(q, 0.0, "strictly_positive_q2")
        before = q.x.array.copy()
        self.assertLess(solver.limiter.control_coefficients(before).min(), 0.0)
        report = solver.limiter.apply(state)
        self.assertEqual(report.scaled_cells, 0)
        self.assertGreaterEqual(report.minimum_after, 0.0)
        self.assertGreaterEqual(report.minimum_scaling_factor, 0.0)
        self.assertLessEqual(report.mean_scaling_factor, 1.0)
        np.testing.assert_array_equal(q.x.array, before)

    def test_q2_limiter_scaling_factors_stay_in_unit_interval(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(cells=(4, 4, 4)), 0.000625, degree=2,
            certificate_mode="adaptive", certificate_max_depth=4,
        )
        state = solver.gaussian_projected(
            (1.0, 1.0, 20.0), np.diag([4.0, 4.0, 9.0]),
            quadrature_degree=14, apply_limiter=False,
        )
        report = solver.limiter.apply(state)
        self.assertGreaterEqual(report.minimum_cell_average, 0.0)
        self.assertGreaterEqual(report.minimum_scaling_factor, 0.0)
        self.assertLessEqual(report.mean_scaling_factor, 1.0)
        self.assertLess(abs(report.mass_before-report.mass_after), 1.0e-13)

    def test_forecast_can_record_an_unlimited_q2_trajectory(self):
        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(cells=(3, 3, 3)), 0.000625, degree=2,
            apply_positivity=False,
        )
        state = solver.gaussian_projected(
            (1.0, 1.0, 20.0), np.diag([4.0, 4.0, 9.0]),
            quadrature_degree=12, apply_limiter=False,
        )
        forecast = solver.step(state)
        self.assertIsNone(solver.last_limiter)
        self.assertEqual(solver.limiter_history_summary(), {"steps": 0})
        np.testing.assert_array_equal(
            solver.limiter.last_raw_coefficients, forecast.function.x.array
        )

    def test_structured_q1_embedding_into_q2_is_exact(self):
        domain = Domain(((-1.0, 1.0),) * 3, (2, 2, 2))
        q1 = FokkerPlanckSolver(Lorenz63Model(), domain, 0.01, degree=1)
        initial = q1.gaussian_interpolated((0.1, -0.2, 0.3), np.diag([0.4, 0.5, 0.6]))
        represented = q1.structured_export(initial, 3)
        q2 = FokkerPlanckSolver(Lorenz63Model(), domain, 0.01, degree=2)
        embedded = q2.from_structured(represented, apply_limiter=False)
        reconstructed = q2.structured_export(embedded, 3)
        np.testing.assert_allclose(reconstructed, represented, rtol=2.0e-12, atol=1.0e-14)

    def test_local_q2_projection_is_conservative_positive_and_minimum_change(self):
        from lorenz_fpe.local_projection import LocalPolynomialProjector

        domain = Domain(((0.0, 1.0),) * 3, (1, 1, 1))
        solver = FokkerPlanckSolver(
            Lorenz63Model(), domain, 0.01, degree=2,
            certificate_mode="adaptive", certificate_max_depth=4,
        )
        q = fem.Function(solver.V)
        q.interpolate(lambda x: (x[0] - 0.37) ** 2 - 0.002 + 0.0 * x[1])
        dofs = solver.V.dofmap.cell_dofs(0)
        raw = q.x.array[dofs].copy()
        result = LocalPolynomialProjector(solver.limiter).project_cell(raw)

        self.assertEqual(result.status, "PROJECTED")
        self.assertLess(
            abs(solver.limiter.cell_average(result.coefficients)
                - solver.limiter.cell_average(raw)),
            1.0e-12,
        )
        self.assertGreaterEqual(
            solver.limiter.control_coefficients(result.coefficients).min(), -1.0e-12
        )
        self.assertLessEqual(result.objective, result.scaling_objective + 1.0e-12)

    def test_local_q2_projection_exposes_negative_average_infeasibility(self):
        from lorenz_fpe.local_projection import LocalPolynomialProjector

        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(((0.0, 1.0),) * 3, (1, 1, 1)),
            0.01, degree=2,
        )
        raw = -np.ones(27)
        result = LocalPolynomialProjector(solver.limiter).project_cell(raw)
        self.assertEqual(result.status, "NEGATIVE_CELL_AVERAGE")
        np.testing.assert_array_equal(result.coefficients, raw)

    def test_local_q2_projection_honours_prescribed_zero_average(self):
        from lorenz_fpe.local_projection import LocalPolynomialProjector

        solver = FokkerPlanckSolver(
            Lorenz63Model(), Domain(((0.0, 1.0),) * 3, (1, 1, 1)),
            0.01, degree=2,
        )
        raw = np.linspace(-1.0e-8, 1.0e-8, 27)
        result = LocalPolynomialProjector(solver.limiter).project_cell(
            raw, prescribed_average=0.0
        )
        self.assertEqual(result.status, "PROJECTED_ZERO_AVERAGE")
        np.testing.assert_array_equal(result.coefficients, np.zeros(27))


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
