import unittest
import tempfile
from pathlib import Path
import numpy as np
from lorenz_fpe import BayesianAnalysis,Domain,FokkerPlanckSolver,Lorenz63Model,ObservationModel

class TestSolverSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=FokkerPlanckSolver(Lorenz63Model(),Domain(cells=(3,4,4)),.01)
    def test_forecast_probability_invariants(self):
        q=self.s.gaussian((1,1,20),np.diag([9,9,25]))
        out=self.s.forecast(q,0,.02); d=self.s.diagnostics(out)
        self.assertLess(abs(d["mass"]-1),1e-9); self.assertGreaterEqual(d["minimum"],-1e-14)
        self.assertLess(d["linear_solver"]["true_relative_residual"],1e-8)
        report=self.s.last_limiter
        self.assertLess(abs(report.mass_before-report.mass_after_stage1),1e-12)
        self.assertLess(abs(report.mass_before-report.mass_after),1e-12)
        for c in range(self.s.mesh.topology.index_map(self.s.mesh.topology.dim).size_local):
            self.assertGreaterEqual(out.function.x.array[self.s.V.dofmap.cell_dofs(c)].min(),-1e-14)
        self.assertGreaterEqual(report.raw_to_final_l1_correction,0.0)
    def test_structured_roundtrip_conserves_mass(self):
        q=self.s.gaussian((1,1,20),np.diag([9,9,25])); a=self.s.structured_export(q)
        r=self.s.from_structured(a)
        self.assertLess(abs(self.s.mass(q)-self.s.mass(r)),1e-12)
    def test_forecast_ksp_tolerances_are_configurable(self):
        solver=FokkerPlanckSolver(
            Lorenz63Model(),Domain(cells=(2,2,2)),.01,
            ksp_rtol=1e-12,ksp_atol=1e-15,
        )
        rtol,atol,_,_=solver.ksp.getTolerances()
        self.assertEqual(rtol,1e-12)
        self.assertEqual(atol,1e-15)
    def test_graded_hex_common_grid_export_is_conservative(self):
        domain=Domain(cells=(2,2,2))
        axes=(
            np.array([-30.0,-15.0,30.0]),
            np.array([-40.0,-20.0,40.0]),
            np.array([-10.0,10.0,70.0]),
        )
        solver=FokkerPlanckSolver(
            Lorenz63Model(),domain,.01,degree=2,axis_coordinates=axes,
        )
        state=solver.gaussian_projected(
            (1.0,1.0,20.0),np.diag([9.0,9.0,25.0]),apply_limiter=False,
        )
        exported=solver.common_grid_export(state,(4,4,4))
        self.assertEqual(exported.shape,(4,4,4))
        self.assertLess(abs(exported.mean()*domain.volume-solver.mass(state)),1e-11)
        self.assertGreater(float(np.max(solver.cell_volumes)),float(np.min(solver.cell_volumes)))
    def test_refined_structured_roundtrip_preserves_q1_shape(self):
        q=self.s.gaussian((1,1,20),np.diag([9,9,25])); a=self.s.structured_export(q,2)
        r=self.s.from_structured(a); difference=q.function-r.function
        self.assertLess(self.s._integral(abs(difference)),1e-12)
        self.assertGreaterEqual(a.min(),-1e-14)
        qd,rd=self.s.diagnostics(q),self.s.diagnostics(r)
        np.testing.assert_allclose(rd["mean"],qd["mean"],rtol=0,atol=1e-11)
        np.testing.assert_allclose(rd["covariance"],qd["covariance"],rtol=0,atol=1e-10)
    def test_checkpoint_and_da_continuity_without_gaussianisation(self):
        q=self.s.gaussian((1,1,20),np.diag([9,9,25]))
        posterior,_=BayesianAnalysis(self.s,ObservationModel.named("x",4.)).update(q,np.array([2.5]))
        coefficients=posterior.function.x.array.copy()
        self.s.forecast(posterior,posterior.time,posterior.time+self.s.dt)
        np.testing.assert_allclose(self.s.p_old.x.array,coefficients,rtol=0,atol=0)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.npz"; posterior.save_native(path); loaded=self.s.load_native(path)
            np.testing.assert_allclose(loaded.function.x.array,coefficients,rtol=0,atol=0)

if __name__=="__main__": unittest.main()
