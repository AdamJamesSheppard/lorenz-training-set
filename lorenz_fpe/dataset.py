"""Sequential Bayesian DA trajectories and leakage-safe dataset manifests."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .core import (BayesianAnalysis, Domain, FokkerPlanckSolver, Lorenz63Model,
                   ObservationModel, TruthSimulator, solver_metadata, write_json)


@dataclass(frozen=True)
class DatasetConfig:
    trajectories: int = 5
    cycles: int = 10
    burn_in: int = 4
    observation_interval: float = 0.05
    observation: str = "xz"
    observation_variance: float = 4.0
    seed: int = 1729
    export_subcells: int = 2
    max_limiter_relative_l1: float = 0.005
    quadrature_degree: int = 14
    analysis_method: str = "projected"


class DatasetSplitter:
    @staticmethod
    def split(trajectory_ids: list[str], seed: int = 1729) -> dict[str,list[str]]:
        ids=np.array(trajectory_ids); rng=np.random.default_rng(seed); rng.shuffle(ids)
        n=len(ids); n_test=max(1,round(.2*n)) if n>=3 else 0; n_val=max(1,round(.2*n)) if n>=3 else 0
        return {"train_trajectory_ids":ids[:n-n_val-n_test].tolist(),
                "validation_trajectory_ids":ids[n-n_val-n_test:n-n_test].tolist(),
                "test_trajectory_ids":ids[n-n_test:].tolist() if n_test else []}


class DatasetGenerator:
    def __init__(self, solver: FokkerPlanckSolver, config: DatasetConfig):
        self.solver, self.config = solver, config

    def generate(self, root: Path) -> dict[str,object]:
        if self.solver.comm.size != 1:
            raise NotImplementedError("Dataset writing currently requires a serial run; the forecast solver itself supports MPI")
        root.mkdir(parents=True,exist_ok=True); traj_ids=[]; samples=[]; posterior_stats=[]
        for j in range(self.config.trajectories):
            tid=f"trajectory_{j:06d}"; traj_ids.append(tid); td=root/"trajectories"/tid; td.mkdir(parents=True,exist_ok=True)
            rng=np.random.default_rng(self.config.seed+10007*j)
            obs_model=ObservationModel.named(self.config.observation,self.config.observation_variance)
            analysis=BayesianAnalysis(self.solver,obs_model,self.config.analysis_method,
                                      self.config.quadrature_degree)
            mean=np.array([1.,1.,20.])+rng.normal(0,[3,3,5]); std=rng.uniform([2,2,3],[5,5,8])
            posterior=self.solver.gaussian_projected(mean,np.diag(std**2),"posterior_0|0",
                quadrature_degree=self.config.quadrature_degree,apply_limiter=True)
            truth0=np.array([1.,1.,20.])+rng.normal(0,[4,4,6])
            times=np.arange(1,self.config.cycles+1)*self.config.observation_interval
            truth=TruthSimulator(self.solver.model).simulate(truth0,times,self.config.seed+10007*j+1)
            observations=np.stack([obs_model.observe(q,rng) for q in truth])
            np.save(td/"truth.npy",truth); np.save(td/"observations.npy",observations); np.save(td/"observation_times.npy",times)
            write_json(td/"trajectory_metadata.json",{"trajectory_id":tid,"seed":self.config.seed+10007*j,
                       "truth_initial":truth0.tolist(),"initial_prior_mean":mean.tolist(),"initial_prior_std":std.tolist(),
                       "observation_model":asdict(obs_model)})
            for k,(target_t,y) in enumerate(zip(times,observations)):
                cycle=td/f"cycle_{k:06d}"; cycle.mkdir(exist_ok=True)
                input_diag=self.solver.diagnostics(posterior)
                input_tensor=self.solver.structured_export(posterior,self.config.export_subcells)
                forecast=self.solver.forecast(posterior,posterior.time,float(target_t))
                target_tensor=self.solver.structured_export(forecast,self.config.export_subcells)
                fd=self.solver.diagnostics(forecast)
                limiter_history=self.solver.limiter_history_summary()
                status="burn_in" if k<self.config.burn_in else "valid_training_sample"
                failures=[]
                if abs(float(fd["mass"])-1)>1e-9: failures.append("failed_mass")
                if float(fd["minimum"]) < -1e-13: failures.append("failed_positivity")
                if float(fd["boundary_mass_fraction"]) > 2e-2: failures.append("failed_boundary")
                if float(fd["linear_solver"].get("true_relative_residual",1))>1e-8: failures.append("failed_solver")
                if limiter_history["relative_l1_correction"]["maximum"]>self.config.max_limiter_relative_l1:
                    failures.append("failed_limiter_severity")
                voxel_volume=self.solver.domain.volume/target_tensor.size
                projection_error=abs(float(target_tensor.sum()*voxel_volume)-float(fd["mass"]))
                if projection_error>1e-11: failures.append("failed_projection")
                if float(input_diag["minimum"]) < -1e-13 or abs(float(input_diag["mass"])-1)>1e-9:
                    failures.append("failed_input_state")
                if failures: status=failures[0]
                posterior_new,ad=analysis.update(forecast,y)
                pd=self.solver.diagnostics(posterior_new)
                posterior_next_tensor=self.solver.structured_export(posterior_new,self.config.export_subcells)
                mode_count=self._mode_count(posterior_next_tensor)
                # Float64 is intentional: these are probability cell averages,
                # and the exported discrete mass should retain FEM accuracy.
                # Downcasting for a particular ML experiment is a later,
                # explicitly validated data-preparation step.
                np.save(cycle/"posterior.npy",input_tensor.astype(np.float64))
                np.save(cycle/"forecast.npy",target_tensor.astype(np.float64))
                posterior.save_native(cycle/"posterior_native.npz")
                forecast.save_native(cycle/"forecast_native.npz")
                posterior_new.save_native(cycle/"posterior_next_native.npz")
                write_json(cycle/"diagnostics.json",{"status":status,"cycle":k,"time":float(target_t),
                    "input_posterior":input_diag,"forecast":fd,"analysis":ad,"posterior_next":pd,
                    "limiter_history":limiter_history,"conservative_projection_mass_error":projection_error})
                record={"trajectory_id":tid,"cycle":k,"physical_time":float(target_t-self.config.observation_interval),
                        "forecast_interval":self.config.observation_interval,"path":str(cycle.relative_to(root)),"status":status}
                samples.append(record)
                posterior_stats.append({"trajectory_id":tid,"cycle":k,"phase":"burn_in" if k<self.config.burn_in else "mature",
                    "covariance_eigenvalues":np.linalg.eigvalsh(np.asarray(pd["covariance"])).tolist(),
                    "l2":pd["l2"],"entropy":pd["entropy_cell_average"],"skewness":pd["marginal_skewness"],
                    "excess_kurtosis":pd["marginal_excess_kurtosis"],"effective_support":pd["effective_support_volume"],
                    "mode_count":mode_count,"boundary_mass_fraction":pd["boundary_mass_fraction"]})
                posterior=posterior_new
                print(f"{tid} | cycle {k:03d} | t={target_t:.3f} | {status} | mass={fd['mass']:.12f} | min={fd['minimum']:.2e} | KSP={fd['linear_solver'].get('ksp_iterations')}",flush=True)
        split=DatasetSplitter.split(traj_ids,self.config.seed)
        valid_samples=[s for s in samples if s["status"]=="valid_training_sample"]
        manifest={"format":"lorenz63_da_operator_v1","sample_definition":"(p_k|k, dt_k) -> p_k+1|k",
                  "primary_distribution":"post-burn-in sequential Bayesian DA posteriors","config":asdict(self.config),
                  **split,"training_samples":valid_samples,"all_cycle_records":samples,
                  "production_readiness":"INSUFFICIENT_EVIDENCE" if not valid_samples else "REQUIRES_CONFIGURATION_LEVEL_VALIDATION",
                  "configuration_validation_required":True,
                  "quality_rule":"Only status=valid_training_sample appears in training_samples; burn-in and every failed state are excluded. Passing a per-cycle gate is necessary but does not certify the solver configuration."}
        write_json(root/"dataset_manifest.json",manifest)
        write_json(root/"dataset_schema.json",{"tensor_axes":["x_cell","y_cell","z_cell"],"tensor_dtype":"float64",
            "tensor_value":"conservative cell-average density",
            "subcells_per_dg_cell":self.config.export_subcells,
            "input":"posterior.npy = p_k|k","target":"forecast.npy = p_k+1|k","split_unit":"complete trajectory"})
        write_json(root/"posterior_distribution_report.json",self._distribution_report(posterior_stats))
        write_json(root/"solver_metadata.json",solver_metadata(self.solver))
        return manifest

    @staticmethod
    def _mode_count(a: np.ndarray, relative_threshold: float = 0.05) -> int:
        """Count strict 26-neighbour voxel maxima above a relative threshold.

        This is a mesh-dependent exploratory multimodality indicator, not a
        topological or statistical test of a continuous density.
        """
        a=np.asarray(a); padded=np.pad(a,1,mode="constant",constant_values=-np.inf)
        is_max=a>relative_threshold*float(a.max())
        for di in (-1,0,1):
            for dj in (-1,0,1):
                for dk in (-1,0,1):
                    if di==dj==dk==0: continue
                    neighbour=padded[1+di:1+di+a.shape[0],1+dj:1+dj+a.shape[1],1+dk:1+dk+a.shape[2]]
                    is_max &= a>neighbour
        return int(is_max.sum())

    @staticmethod
    def _distribution_report(rows: list[dict[str,object]]) -> dict[str,object]:
        report={"purpose":"compare startup and post-burn-in DA posterior families; a preliminary burn-in diagnostic, not proof of stationarity"}
        for phase in ("burn_in","mature"):
            subset=[r for r in rows if r["phase"]==phase]
            eig=np.array([r["covariance_eigenvalues"] for r in subset],float)
            report[phase]={"count":len(subset),"mean_covariance_eigenvalues":eig.mean(axis=0).tolist() if len(eig) else [],
                           "mean_l2":float(np.mean([r["l2"] for r in subset])) if subset else None,
                           "mean_entropy":float(np.mean([r["entropy"] for r in subset])) if subset else None,
                           "mean_effective_support_volume":float(np.mean([r["effective_support"] for r in subset])) if subset else None,
                           "mean_mode_count":float(np.mean([r["mode_count"] for r in subset])) if subset else None,
                           "mean_absolute_skewness":np.mean(np.abs(np.array([r["skewness"] for r in subset],float)),axis=0).tolist() if subset else [],
                           "mean_excess_kurtosis":np.mean(np.array([r["excess_kurtosis"] for r in subset],float),axis=0).tolist() if subset else [],
                           "mean_boundary_mass_fraction":float(np.mean([r["boundary_mass_fraction"] for r in subset])) if subset else None}
        return report
