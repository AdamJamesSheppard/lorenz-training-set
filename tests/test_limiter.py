import unittest
import numpy as np
from lorenz_fpe.core import PositivityLimiter
from lorenz_fpe.dataset import DatasetSplitter

class TestProjection(unittest.TestCase):
    def test_positive_and_conservative(self):
        w=np.array([.4,-.2,.1,.7]); v=np.array([1.,2.,3.,4.])
        x=PositivityLimiter.project_cell_averages(w,v)
        self.assertGreaterEqual(x.min(),-1e-14)
        self.assertAlmostEqual(float(v@x),float(v@w),places=13)
    def test_identity(self):
        w=np.array([.1,.2]); np.testing.assert_array_equal(PositivityLimiter.project_cell_averages(w,np.ones(2)),w)
    def test_roundoff_repair_cannot_create_negative_active_entries(self):
        # Regression for a first-step Q2 failure where the final unconstrained
        # residual correction drove tiny active entries below zero.
        w=np.array([-1.9245607759411536e-22, 1.0e-20, 0.25, 0.75])
        v=np.array([1.0, 2.0, 3.0, 4.0])
        x=PositivityLimiter.project_cell_averages(w,v)
        self.assertGreaterEqual(x.min(),0.0)
        self.assertLessEqual(abs(float(v@x)-float(v@w)),5e-16)
    def test_trajectory_split_is_disjoint(self):
        s=DatasetSplitter.split([f"trajectory_{i}" for i in range(10)],7)
        groups=[set(s[k]) for k in ("train_trajectory_ids","validation_trajectory_ids","test_trajectory_ids")]
        self.assertTrue(all(not groups[i]&groups[j] for i in range(3) for j in range(i)))
        self.assertEqual(len(set.union(*groups)),10)

if __name__=="__main__": unittest.main()
