#!/usr/bin/env python3
"""Replay the fine mature run, build a time-aggregated grid, and run level three."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml


ROOT=Path(__file__).resolve().parent
REFERENCE=ROOT/"runs/local-q2-cn-full-spd-mature-bimodal/20260913T185157Z/reference"
UNIFORM_REPORT=ROOT/"runs/mature-full-spd-uniform60-reference/20260914T190730Z/mature_bimodal_q2_local_qp_60x72x72/report.json"
FINE_REPORT=ROOT/"runs/mature-full-spd-graded-fine-comparison/20260914T231639Z/mature_bimodal_q2_local_qp_graded58x68x56/report.json"
FINE_AXES=ROOT/"experiments/mature-graded-fine-axes.json"
PIPELINE_SPEC=ROOT/"experiments/mature-time-aggregated-level3-pipeline.yaml"
NOISE=[
    1.4142135623730951,0.0,0.0,
    0.5656854249492381,1.2961481396815722,0.0,
    0.28284271247461906,0.3394673699166024,1.3434142714594956,
]
SNAPSHOTS=list(range(0,321,32))
UNIFORM60_CELLS=60*72*72
AXIS_ENERGY_COVERAGES=(0.90,0.85,0.80,0.75)


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def run_logged(command: list[str], log: Path) -> None:
    with log.open("w") as stream:
        completed=subprocess.run(
            command,cwd=ROOT,text=True,stdout=stream,stderr=subprocess.STDOUT,
            env={**os.environ,"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1",
                 "MKL_NUM_THREADS":"1"},
        )
    if completed.returncode:
        raise RuntimeError(f"command failed with return code {completed.returncode}: {log}")


def normalized(values: np.ndarray) -> np.ndarray:
    norm=float(np.linalg.norm(values.ravel()))
    return values/norm if norm>0.0 else np.zeros_like(values)


def aggregate_indicators(snapshot_dir: Path) -> tuple[np.ndarray,dict[str,object]]:
    aggregate=None; summaries=[]
    for step in SNAPSHOTS:
        path=snapshot_dir/f"indicator_step_{step:04d}.npz"
        with np.load(path) as item:
            correction=np.asarray(item["correction_l1"])
            negative=np.asarray(item["negative_witness_mass"])
            high_mode=np.asarray(item["high_mode_l1"])
            jump=np.asarray(item["jump_indicator"])
            score=(normalized(correction)+normalized(negative)
                   +0.25*normalized(high_mode)+0.25*normalized(jump))
            aggregate=score if aggregate is None else np.maximum(aggregate,score)
            summaries.append({
                "step":step,"time":float(item["time"]),
                "correction_l1_sum":float(correction.sum()),
                "negative_witness_probability_mass":float(negative.sum()),
                "high_mode_l1_sum":float(high_mode.sum()),
                "jump_indicator_sum":float(jump.sum()),
                "sha256":sha256(path),
            })
    if aggregate is None:
        raise RuntimeError("no indicator snapshots were loaded")
    return aggregate,{"snapshots":summaries,
        "formula":"max_t(normalized correction L1 + normalized witness mass + 0.25 normalized high-mode L1 + 0.25 normalized jump)",
        "weights":{"negative_witness_mass":1.0,"high_mode_l1":0.25,"jump":0.25}}


def _axis_band(
    profile: np.ndarray, native_edges: np.ndarray, common_cells: int,
    coverage: float,
) -> tuple[int,int]:
    total=float(profile.sum())
    if total<=0.0:
        raise RuntimeError("Dorfler marking produced an empty axis profile")
    cumulative=np.cumsum(profile)
    tail=0.5*(1.0-coverage)*total
    lo_active=int(np.searchsorted(cumulative,tail,side="right"))
    hi_active=int(np.searchsorted(cumulative,total-tail,side="left"))
    lo_cell=max(0,lo_active-2)
    hi_cell=min(len(native_edges)-2,hi_active+2)
    lo=int(native_edges[lo_cell]); hi=int(native_edges[hi_cell+1])
    # Coarse exterior cells span six common voxels. Align transitions to those
    # cells so every hexahedron remains affine and conforming.
    return max(0,6*(lo//6)),min(common_cells,6*math.ceil(hi/6))


def _edges_for_band(lo: int, hi: int, common_cells: int) -> list[int]:
    edges=(list(range(0,lo,6))+list(range(lo,hi,1))
           +list(range(hi,common_cells+1,6)))
    edges=sorted(set(edges+[0,common_cells]))
    if edges[-1]!=common_cells or any(b<=a for a,b in zip(edges,edges[1:])):
        raise RuntimeError("invalid generated tensor axis")
    return edges


def design_axes(aggregate: np.ndarray) -> tuple[dict[str,object],tuple[int,int,int]]:
    theta=0.5
    flat=np.argsort(aggregate.ravel())[::-1]
    energy=np.square(aggregate.ravel()[flat]); cumulative=np.cumsum(energy)
    count=int(np.searchsorted(cumulative,theta*cumulative[-1])+1)
    marked=np.zeros(aggregate.size,dtype=bool); marked[flat[:count]]=True
    marked=marked.reshape(aggregate.shape)
    old=json.loads(FINE_AXES.read_text())
    common=tuple(old["common_shape"])
    marked_energy=np.where(marked,np.square(aggregate),0.0)
    profiles=[]
    for axis in range(3):
        other=tuple(index for index in range(3) if index!=axis)
        profiles.append(marked_energy.sum(axis=other))
    selected=None
    for coverage in AXIS_ENERGY_COVERAGES:
        output_edges={}; boxes=[]
        for axis,name in enumerate(("x","y","z")):
            native_edges=np.asarray(old["edge_indices"][name],dtype=int)
            lo,hi=_axis_band(profiles[axis],native_edges,common[axis],coverage)
            output_edges[name]=_edges_for_band(lo,hi,common[axis])
            boxes.append([lo,hi])
        cells=tuple(len(output_edges[name])-1 for name in ("x","y","z"))
        if int(np.prod(cells))<=UNIFORM60_CELLS:
            selected=(coverage,output_edges,boxes,cells)
            break
    if selected is None:
        raise RuntimeError(
            "time-aggregated refined bands exceed the frozen uniform-60 cell ceiling"
        )
    coverage,output_edges,boxes,cells=selected
    design={
        "source_replay":"fine 58x68x56 trajectory with snapshots every 32 steps",
        "source_axes_sha256":sha256(FINE_AXES),"common_shape":list(common),
        "edge_indices":output_edges,"native_cells":list(cells),
        "selection":{"dorfler_theta":theta,"marked_cells":count,
            "marked_fraction":count/aggregate.size,"two_native_cell_buffer":True,
            "axis_marked_energy_coverage":coverage,
            "axis_marked_energy_coverage_candidates":list(AXIS_ENERGY_COVERAGES),
            "maximum_native_cells":UNIFORM60_CELLS,
            "refined_common_grid_index_bands":boxes,
            "fine_common_grid_span":1,"coarse_common_grid_span":6},
    }
    return design,cells


def generated_config(axis_path: Path, cells: tuple[int,int,int]) -> dict[str,object]:
    return {
        "id":"mature-full-spd-graded-time-aggregated-level3",
        "kind":"mature_graded_q2_study",
        "status":"predeclared_time_aggregated_density_convergence_gate",
        "purpose":"Third mature level using a maximum-over-time correction, witness, high-mode and jump indicator from the deterministic fine-run replay.",
        "study":{
            "cells":list(cells),"axis_coordinates":str(axis_path),
            "dt":0.00015625,"final_time":0.05,"seed":20260920,
            "monte_carlo_paths":1000000,"mc_dt":0.000125,
            "bootstrap_replicates":1000,"bootstrap_seed":20261920,
            "certificate_max_depth":4,"ksp_rtol":1.0e-12,"ksp_atol":1.0e-15,
            "initialization":"mixture_projected","initial_quadrature_degree":14,
            "common_comparison_grid":[180,216,216],
            "density_metric_grid":[20,24,24],"density_smoothing_sigma":0.75,
            "reference_reuse":str(REFERENCE.relative_to(ROOT)),"noise_matrix":NOISE,
            "branches":[{
                "name":"mature_bimodal_q2_local_qp_time_aggregated_level3",
                "cells":list(cells),"axis_coordinates":str(axis_path),
                "common_export_grid":[180,216,216],"export_subcells":3,
                "degree":2,"theta":0.5,"positivity_method":"local_qp",
                "optimizer_backend":"osqp","optimizer_ftol":1.0e-10,
                "maximum_iterations":10000,"archive_raw":False,
                "comparator_report":str(UNIFORM_REPORT.relative_to(ROOT)),
                "secondary_comparator_name":"graded58x68x56",
                "secondary_comparator_report":str(FINE_REPORT.relative_to(ROOT)),
            }],
        },
        "execution":{"mpi_ranks":8,"numerical_threads":1},
        "scientific_decision":{
            "maximum_step_mass_change":1.0e-12,"maximum_absolute_mass_error":1.0e-10,
            "maximum_negative_mass":1.0e-13,"maximum_normalized_covariance_error":0.08,
            "maximum_covariance_error_to_mc_p95_ratio":5.0,
            "maximum_mean_relative_l1_correction":0.0008,
            "maximum_relative_l1_correction":0.005,
            "maximum_off_diagonal_correlation_error":0.08,
            "maximum_marginal_tv":0.05,"maximum_lobe_probability_error":0.025,
            "maximum_smoothed_joint_tv":0.15,"maximum_initial_projection_joint_tv":0.10,
            "comparator_limits":{"maximum_covariance_error_increase":0.005,
                "maximum_lobe_error_increase":0.005,"maximum_joint_tv_increase":0.005,
                "maximum_marginal_tv_increase":0.005,"maximum_dg_dof_ratio":1.0,
                "maximum_forecast_runtime_ratio":1.0,"maximum_peak_rank_memory_ratio":1.0},
            "secondary_comparator_limits":{"maximum_common_grid_density_l1":0.05434004396153797,
                "maximum_covariance_error_increase":0.005,"maximum_lobe_error_increase":0.005,
                "maximum_joint_tv_increase":0.005,"maximum_marginal_tv_increase":0.005},
        },
        "research_gates":[
            "D_gf,gff must be below 0.5 D_60,gf = 0.05434004396153797.",
            "Mean correction must remain below 0.0008 with zero negativity, failures and fallbacks.",
            "Statistics may not degrade by more than 0.005 from uniform-60 or graded58x68x56.",
            "Runtime, peak rank memory and DG unknowns should remain below uniform-60.",
        ],
        "decision_rule":"Passing supplies a third contracting mature-density level; dataset generation remains unauthorized pending domain sensitivity.",
    }


def main() -> int:
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    work=ROOT/"runs/mature-time-aggregated-grid-pipeline"/stamp
    replay=work/"fine_replay"; snapshots=work/"indicator_snapshots"
    work.mkdir(parents=True)
    metadata={"created_utc":datetime.now(timezone.utc).isoformat(),
        "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "stage":"fine_replay_running","snapshot_steps":SNAPSHOTS,
        "pipeline_spec":str(PIPELINE_SPEC.relative_to(ROOT)),
        "pipeline_spec_sha256":sha256(PIPELINE_SPEC)}
    (work/"pipeline_status.json").write_text(json.dumps(metadata,indent=2)+"\n")
    common=[
        "--cells","58","68","56","--dt","0.00015625","--t-final","0.05",
        "--seed","20260920","--branch","fine_replay_for_time_aggregated_indicator",
        "--degree","2","--theta","0.5","--ksp-rtol","1e-12","--ksp-atol","1e-15",
        "--certificate-mode","fixed","--certificate-max-depth","4",
        "--initialization","mixture_projected","--initial-quadrature-degree","14",
        "--export-subcells","3","--mc-particles",str(REFERENCE/"mc_final_particles.npy"),
        "--bootstrap","1000","--bootstrap-seed","20261920",
        "--density-metric-grid","20","24","24","--density-smoothing-sigma","0.75",
        "--output",str(replay),"--noise-matrix",*map(str,NOISE),
        "--axis-coordinates",str(FINE_AXES),"--common-export-grid","180","216","216",
        "--mixture",str(REFERENCE/"mature_mixture.json"),
        "--initial-mc-particles",str(REFERENCE/"mc_initial_particles.npy"),
        "--local-projection","--local-optimizer-backend","osqp",
        "--local-optimizer-ftol","1e-10","--local-maximum-iterations","10000",
        "--no-raw-archive","--indicator-snapshot-steps",*map(str,SNAPSHOTS),
        "--indicator-output",str(snapshots),
    ]
    run_logged(["mpiexec","-n","8",sys.executable,str(ROOT/"same_mesh_q2_study.py"),
                "forecast",*common],work/"fine_replay.log")
    metadata["stage"]="designing_level3"; (work/"pipeline_status.json").write_text(
        json.dumps(metadata,indent=2)+"\n"
    )
    aggregate,indicator_metadata=aggregate_indicators(snapshots)
    np.save(work/"time_aggregated_indicator.npy",aggregate)
    design,cells=design_axes(aggregate); design["indicator"]=indicator_metadata
    axis_path=work/"time_aggregated_level3_axes.json"
    axis_path.write_text(json.dumps(design,indent=2)+"\n")
    config=generated_config(axis_path,cells)
    config_path=work/"time_aggregated_level3_config.yaml"
    config_path.write_text(yaml.safe_dump(config,sort_keys=False))
    metadata.update({"stage":"level3_running","generated_cells":list(cells),
        "generated_dg_dofs":int(np.prod(cells)*27),"axis_sha256":sha256(axis_path),
        "config_sha256":sha256(config_path)})
    (work/"pipeline_status.json").write_text(json.dumps(metadata,indent=2)+"\n")
    run_logged([sys.executable,str(ROOT/"scripts/run_experiment.py"),str(config_path)],
               work/"level3_launcher.log")
    metadata["stage"]="complete"; (work/"pipeline_status.json").write_text(
        json.dumps(metadata,indent=2)+"\n"
    )
    print(work)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
