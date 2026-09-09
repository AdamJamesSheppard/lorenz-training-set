import json,os,shutil,subprocess,sys,unittest
from pathlib import Path

class TestMPIConsistency(unittest.TestCase):
    def _run(self,ranks):
        worker=Path(__file__).with_name("mpi_probe_worker.py")
        cmd=[sys.executable,str(worker)] if ranks==1 else [shutil.which("mpirun"),"--allow-run-as-root","-n",str(ranks),sys.executable,str(worker)]
        env=dict(os.environ); env["PYTHONPATH"]=str(worker.parent.parent)+os.pathsep+env.get("PYTHONPATH","")
        p=subprocess.run(cmd,cwd=worker.parent.parent,env=env,text=True,capture_output=True,timeout=45,check=True)
        line=next(x for x in p.stdout.splitlines() if x.startswith("MPI_PROBE="))
        return json.loads(line.split("=",1)[1])
    @unittest.skipUnless(shutil.which("mpirun"),"mpirun unavailable")
    def test_two_rank_limiter_agrees_with_serial(self):
        a,b=self._run(1),self._run(2)
        self.assertAlmostEqual(a["mass"],b["mass"],places=9)
        self.assertAlmostEqual(a["l2"],b["l2"],places=9)
        self.assertAlmostEqual(a["relative_l1_correction"],b["relative_l1_correction"],places=9)
        for x,y in zip(a["mean"],b["mean"]): self.assertAlmostEqual(x,y,places=8)
        self.assertGreaterEqual(b["minimum"],-1e-13)

if __name__=="__main__": unittest.main()
