import unittest
from lorenz_fpe.validation import analytic_benchmarks

class TestAnalyticBenchmarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=analytic_benchmarks((6,6,6),.01,.02)
    def test_pure_diffusion(self):
        r=self.r["pure_diffusion"]
        self.assertLess(r["mass_error"],1e-9); self.assertGreater(r["minimum"],-1e-13)
        self.assertLess(r["l1_error"],.8)
    def test_constant_advection_diffusion(self):
        r=self.r["constant_advection_diffusion"]
        self.assertLess(r["mass_error"],1e-9); self.assertGreater(r["minimum"],-1e-13)
        self.assertLess(r["l1_error"],.8)
    def test_non_gaussian(self):
        r=self.r["non_gaussian"]
        self.assertLess(r["mass_error"],1e-9); self.assertGreater(r["minimum"],-1e-13)

if __name__=="__main__": unittest.main()
