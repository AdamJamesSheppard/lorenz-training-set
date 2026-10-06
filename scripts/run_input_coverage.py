"""Frozen grouped G03 characterization; no scientific qualification or training."""
import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from operator_learning.alignment import density_summary, distance
from operator_learning.governance import check_repository, validate_predeclaration, validate_provenance
from operator_learning.reconstruction import dense_occupation
from operator_learning.reconstruction_controls import empirical_box_density, restart_path
from scripts.run_reconstruction_qualification import bounds, git, sha, verify_sources
from scripts.run_input_diversity import resolution_margin


def grouped_coverage(laws, pairs, order, sizes, eligible=None):
    """Fixed group allocation; no outcome-driven selection or cross-group leakage."""
    if len(set(order)) != len(order) or set(order) != {x['seed'] for x in laws}:
        raise ValueError('Order must contain every source group exactly once')
    lookup = {frozenset(x['laws']): x for x in pairs}
    results = []
    for size in sizes:
        if not 0 < size < len(order):
            raise ValueError('Pool must leave other source groups')
        selected = set(order[:size])
        train = [x for x in laws if x['seed'] in selected and (eligible is None or x['id'] in eligible)]
        queries = [x for x in laws if x['seed'] not in selected]
        rows = []
        for q in queries:
            candidates = [lookup[frozenset((q['id'], t['id']))] for t in train
                          if frozenset((q['id'], t['id'])) in lookup
                          and (eligible is None or q['id'] in eligible)]
            best = min(candidates, key=lambda x: x['tv']) if candidates else None
            rows.append(dict(law=q['id'], status='MEASURED_QUERY' if best else 'UNAVAILABLE',
                             nearest_pair=best['laws'] if best else None,
                             tv=best['tv'] if best else None))
        values = [x['tv'] for x in rows if x['tv'] is not None]
        results.append(dict(group_count=size, selected_groups=order[:size],
                            attempted_queries=len(queries), measured_queries=len(values),
                            rows=rows, summary=quantiles(values)))
    return results


def quantiles(values):
    return {k: float(np.quantile(values, q)) if values else None
            for k, q in [('median', .5), ('p90', .9), ('p95', .95), ('maximum', 1)]}


def boundary_probability(field, domain, thickness):
    """Exact common-region integral of the piecewise-constant voxel density."""
    inside = np.ones(field.shape)
    dv = 1.
    for axis, ((lo, hi), n, width) in enumerate(zip(domain, field.shape, thickness)):
        if not 0 < width < (hi-lo)/2:
            raise ValueError('Positive boundary thickness below half side required')
        edges = np.linspace(lo, hi, n+1)
        h = (hi-lo)/n
        fraction = np.maximum(0., np.minimum(edges[1:], hi-width)
                              - np.maximum(edges[:-1], lo+width))/h
        shape = [1]*3
        shape[axis] = n
        inside *= fraction.reshape(shape)
        dv *= h
    return float((field*(1-inside)).sum()*dv)


def validate(config):
    validate_predeclaration(config)
    seeds = config['seeds']['trajectory']
    if (config['gate_id'] != 'OL-G03_INPUT_DIVERSITY'
            or config['scientific_adjudication'] != 'CHARACTERIZATION_ONLY_G03_OPEN'
            or seeds != list(range(83001, 83013)) or config['windows'] != 3
            or config['spinup'] != 20 or config['window'] != 10
            or config['integration_steps'] != [.000125, .00025]
            or config['physical_widths'] != [4, 40/9, 40/9]
            or config['sampling_count'] != 20000 or config['control_count'] != 80000
            or config['phases'] != [0, 1, 2, 3]
            or config['pool_sizes'] != [2, 4, 8]
            or config['comparison_shapes'] != [[60,72,72], [120,144,144]]):
        raise ValueError('Frozen hierarchical characterization differs')
    if len(config['group_orders']) != 2 or any(sorted(x) != seeds for x in config['group_orders']):
        raise ValueError('Two complete group permutations required')


def prepare(source):
    config = json.loads(source.read_text())
    validate(config)
    if check_repository(ROOT):
        raise ValueError('Governance inconsistency')
    rel = str(source.resolve().relative_to(ROOT))
    if subprocess.check_output(['git', 'show', 'HEAD:'+rel], cwd=ROOT) != source.read_bytes():
        raise ValueError('Committed config required')
    verify_sources(config)
    record = dict(experiment_id=config['id'], gate_id=config['gate_id'], kind=config['kind'],
        config_sha256=sha(source), git_commit=git('rev-parse','HEAD'),
        git_dirty=bool(git('status','--porcelain')), git_status=git('status','--porcelain'),
        command=config['command'], runtime_versions=config['runtime_versions'],
        hardware=config['hardware'], seeds=config['seeds'], input_hashes=config['inputs'],
        output_hashes={}, checkpoint_hashes={}, diagnostics={}, status='PREPARED_NOT_EXECUTED')
    validate_provenance(record)
    run = ROOT/'runs/operator-learning'/config['id']/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True, exist_ok=False)
    (run/'config.json').write_bytes(source.read_bytes())
    (run/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    return run


def execute(run):
    config = json.loads((run/'config.json').read_text())
    provenance = json.loads((run/'provenance.json').read_text())
    validate(config)
    verify_sources(config)
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    if (provenance['status'] != 'PREPARED_NOT_EXECUTED' or versions != config['runtime_versions']
            or sha(run/'config.json') != provenance['config_sha256']
            or git('rev-parse','HEAD') != provenance['git_commit']):
        raise ValueError('Frozen runtime/source mismatch')
    if any(os.environ.get(k) != '1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')):
        raise ValueError('One CPU thread required')
    start = time.monotonic()
    write = lambda n,x: (run/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
    outputs, laws, attempts, errors, within, pairs, coverage = {}, [], [], [], [], [], []
    def save(name, **arrays):
        np.savez_compressed(run/name, **arrays)
        outputs[name] = sha(run/name)
    def progress():
        write('partial_report.json',dict(attempts=attempts, errors=errors, exclusions=[],
                                       elapsed_seconds=time.monotonic()-start))
    provenance.update(status='RUNNING', actual_command=sys.argv,
                      observed_runtime_versions=versions, observed_hardware=platform.platform())
    write('provenance.json',provenance)
    try:
        for seed in config['seeds']['trajectory']:
            print(f'seed{seed} path generation starting elapsed={time.monotonic()-start:.1f}s',flush=True)
            try:
                original, spin = dense_occupation(seed,config['spinup'],.001,.001)
                initial = spin[0].copy()
                total = config['windows']*config['window']
                fine = restart_path(initial,total,config['integration_steps'][0])
                coarse = restart_path(initial,total,config['integration_steps'][1])
                save(f'seed{seed}_paths.npz',original=original,initial=initial,fine=fine,coarse=coarse)
            except Exception as error:
                errors.append(dict(seed=seed,stage='PATH_GENERATION',error=repr(error)))
                for w in range(config['windows']):
                    attempts.append(dict(seed=seed,window=w,status='FAILED_PATH',error=repr(error)))
                progress()
                continue
            for w in range(config['windows']):
                ident = f'seed{seed}_window{w}'
                row = dict(id=ident,seed=seed,window=w,status='RUNNING',grids=[])
                attempts.append(row)
                cloud = fine[w*80000:(w+1)*80000]
                control = coarse[w*40000:(w+1)*40000]
                try:
                    bound = bounds(cloud,control,config['sampling_count'],config['physical_widths'])
                    row.update(bound=bound,reconstruction_resolved=bound['total_tv_upper'] <= config['thresholds']['reconstruction_tv_max'])
                    for shape in config['comparison_shapes']:
                        name = ident+'_grid'+'x'.join(map(str,shape))+'.npz'
                        arrays, raw = {}, []
                        phases = config['phases'] if shape==config['comparison_shapes'][0] else [3]
                        for phase in phases:
                            field,mass = empirical_box_density(cloud[phase::4],config['bounds'],config['physical_widths'],shape)
                            if not np.isfinite(field).all() or field.min()<0 or abs(mass-1)>config['thresholds']['mass_error_max']:
                                raise ValueError('Raw invariant failure; no repair')
                            arrays[f'phase{phase}'] = field
                            raw.append(dict(phase=phase,mass=mass,negative_mass=0.))
                        if len(phases)==4:
                            for a,b in combinations(phases,2):
                                metrics=distance(arrays[f'phase{a}'],arrays[f'phase{b}'],config['bounds'])
                                within.append(dict(law=ident,phases=[a,b],tv=metrics['l1']/2,metrics=metrics))
                        field=arrays['phase3']
                        summary=density_summary(field,config['bounds'],**config['regions'])
                        summary['boundary_probability']=boundary_probability(field,config['bounds'],config['boundary_thickness'])
                        row['grids'].append(dict(shape=shape,path=name,raw=raw,summary=summary))
                        save(name,**arrays)
                        del arrays,field
                    row['status']='COMPLETED'
                    laws.append(row)
                except Exception as error:
                    row.update(status='FAILED',error=repr(error))
                    errors.append(dict(law=ident,error=repr(error)))
                progress()
                print(f'{ident} {row["status"]} elapsed={time.monotonic()-start:.1f}s',flush=True)
            del fine,coarse
        # Stream two archives at a time: no 36-field high-resolution RAM stack.
        for a,b in combinations(laws,2):
            with np.load(run/a['grids'][0]['path']) as aa, np.load(run/b['grids'][0]['path']) as bb:
                metrics=distance(aa['phase3'],bb['phase3'],config['bounds'])
            tv=metrics['l1']/2
            mass=lambda row:next(x['mass'] for x in row['grids'][0]['raw'] if x['phase']==3)
            sa,sb=a['grids'][0]['summary'],b['grids'][0]['summary']
            pairs.append(dict(laws=[a['id'],b['id']],family='WITHIN_SOURCE' if a['seed']==b['seed'] else 'CROSS_SOURCE',
                tv=tv,metrics=metrics,mean_error=float(np.linalg.norm(np.array(sa['mean'])-sb['mean'])),
                covariance_error=float(np.linalg.norm(np.array(sa['covariance'])-sb['covariance'])),
                statistic_errors={k:abs(sa[k]-sb[k]) for k in ['positive_x_probability','tail_probability','transition_probability','boundary_probability']},
                **resolution_margin(tv,a['bound']['total_tv_upper'],b['bound']['total_tv_upper'],mass(a),mass(b))))
        # Missing laws remain queries/denominators in allocation reports.
        all_laws=[dict(id=f'seed{s}_window{w}',seed=s) for s in config['seeds']['trajectory'] for w in range(config['windows'])]
        eligible={x['id'] for x in laws if x['reconstruction_resolved']}
        for order in config['group_orders']:
            coverage.append(dict(order=order,all_attempts=grouped_coverage(all_laws,pairs,order,config['pool_sizes']),
                                 resolved_only=grouped_coverage(all_laws,pairs,order,config['pool_sizes'],eligible)))
        export=[]
        for row in laws:
            with np.load(run/row['grids'][0]['path']) as a,np.load(run/row['grids'][1]['path']) as b:
                fine_grid=b['phase3']; restricted=fine_grid.reshape(60,2,72,2,72,2).mean(axis=(1,3,5))
                export.append(dict(law=row['id'],metrics=distance(a['phase3'],restricted,config['bounds']),
                                   interpretation='aligned conservative export consistency, not subvoxel fidelity'))
        report=dict(attempts=attempts,laws=laws,errors=errors,exclusions=[],within=within,pairs=pairs,coverage=coverage,
            export=export,expected_laws=36,expected_within=216,expected_pairs=630,
            pair_summaries={f:quantiles([x['tv'] for x in pairs if x['family']==f]) for f in ['WITHIN_SOURCE','CROSS_SOURCE']},
            technical_status='COMPLETED' if len(laws)==36 and not errors else 'COMPLETED_WITH_FAILURES',
            scientific_qualification=False,gate_status='OPEN',elapsed_seconds=time.monotonic()-start,limitations=config['limitations'])
        write('report.json',report)
        outputs['report.json']=sha(run/'report.json')
        outputs['partial_report.json']=sha(run/'partial_report.json')
        provenance.update(status='COMPLETED',output_hashes=outputs,diagnostics=dict(technical_status=report['technical_status'],gate_passed=False))
        validate_provenance(provenance)
        write('provenance.json',provenance)
        write('seal.json',{n:sha(run/n) for n in ['config.json','provenance.json',*outputs]})
        print('G03_COVERAGE_COMPLETED_GATE_OPEN',flush=True)
    except Exception as error:
        errors.append(dict(stage='RUN',error=repr(error)))
        progress()
        provenance.update(status='FAILED',diagnostics=dict(errors=errors))
        write('provenance.json',provenance)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path',type=Path)
    parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    print(prepare(args.path.resolve())) if args.prepare else execute(args.path.resolve())
