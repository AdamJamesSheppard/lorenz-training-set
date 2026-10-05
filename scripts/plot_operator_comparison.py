"""Archived pilot density comparison; infer/render use separate existing runtimes.

No solver execution, retraining, trajectory synthesis or historical-output edits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = [(-30, 30), (-40, 40), (-10, 70)]
VOLUME = 384000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer(source, output):
    import torch
    sys.path.insert(0, str(ROOT / 'scripts'))
    from train_neural_pilot import Operator, metrics

    output.mkdir(parents=True, exist_ok=False)
    trainer = ROOT / 'scripts/train_neural_pilot.py'
    originals = json.loads((source / 'input_sha256.json').read_text())
    if sha(trainer) != originals[str(trainer)]:
        raise ValueError('Checkpoint implementation differs from historical trainer')
    manifest = json.loads((source / 'manifest.json').read_text())
    checkpoint = source / 'best_model.pt'
    torch.set_num_threads(2)
    model = Operator().cpu().eval()
    model.load_state_dict(torch.load(checkpoint, map_location='cpu', weights_only=True)['model'])
    records = []
    for index in (4, 5):
        entry = manifest[index]
        pairpath = source / entry['path']
        if sha(pairpath) != entry['sha256']:
            raise ValueError('Historical pair hash mismatch')
        with np.load(pairpath) as pair:
            initial, target = pair['initial'].copy(), pair['final'].copy()
        with torch.no_grad():
            prediction = model(torch.from_numpy(initial * VOLUME)[None, None])
        learned = prediction.numpy()[0, 0] / VOLUME
        path = output / f'law{index}_fields.npz'
        np.savez(path, initial=initial, target=target, learned=learned)
        records.append(dict(law=index, split=entry['split'], source_pair=entry['path'],
                            source_sha256=sha(pairpath), derived=path.name,
                            derived_sha256=sha(path), cpu_metrics=metrics(
                                prediction, torch.from_numpy(target * VOLUME)[None, None])))
    report = dict(source_run=str(source), checkpoint_sha256=sha(checkpoint),
                  trainer_sha256=sha(trainer), script_sha256=sha(Path(__file__)),
                  git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  git_status=subprocess.check_output(['git', 'status', '--short'], text=True),
                  torch_version=torch.__version__, numpy_version=np.__version__,
                  inference_device='cpu', forecast_time=.05, bounds=BOUNDS,
                  rendering_seed=1963, records=records,
                  limitations=['FEM is its conservative 60x72x72 learning representation',
                               'CPU inference may differ slightly from archived CUDA scores',
                               '3D points are density-visualization draws, not truth trajectories',
                               'Original test law has been inspected; no qualification gate pass'])
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')


def render(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm, TwoSlopeNorm

    report = json.loads((output / 'provenance.json').read_text())
    fields = []
    for entry in report['records']:
        path = output / entry['derived']
        if sha(path) != entry['derived_sha256']:
            raise ValueError('Derived fields changed')
        with np.load(path) as data:
            fields.append({k: data[k].astype(float) for k in ('initial', 'target', 'learned')})
    shape = fields[0]['target'].shape
    widths = [(hi-lo)/n for (lo, hi), n in zip(BOUNDS, shape)]
    edges = [np.linspace(lo, hi, n+1) for (lo, hi), n in zip(BOUNDS, shape)]
    labels = ['Input density (t=0)', 'FEM forecast (t=0.05)', 'Learned forecast (t=0.05)']
    plt.rcParams.update({'font.size': 10, 'axes.titlesize': 11})
    # Joint marginals integrate the actual conservative voxels, no KDE smoothing.
    for entry, data in zip(report['records'], fields):
        fig, axes = plt.subplots(3, 4, figsize=(17, 10), layout='constrained')
        for row, (a, b, integrate) in enumerate(((0, 2, 1), (0, 1, 2), (1, 2, 0))):
            maps = [data[k].sum(axis=integrate) * widths[integrate]
                    for k in ('initial', 'target', 'learned')]
            vmax = max(p.max() for p in maps)
            norm = LogNorm(vmin=1e-6, vmax=vmax)
            for column, p in enumerate(maps):
                ax = axes[row, column]
                mesh = ax.pcolormesh(edges[a], edges[b], np.ma.masked_less_equal(p.T, 0),
                                     cmap='magma', norm=norm, shading='flat')
                ax.set(xlabel='xyz'[a], ylabel='xyz'[b], title=labels[column])
            fig.colorbar(mesh, ax=axes[row, :3], label='Joint density (shared log scale)')
            error = maps[2] - maps[1]
            maxerr = float(np.abs(error).max())
            ax = axes[row, 3]
            errmesh = ax.pcolormesh(edges[a], edges[b], error.T, cmap='RdBu_r',
                                    norm=TwoSlopeNorm(vcenter=0, vmin=-maxerr, vmax=maxerr),
                                    shading='flat')
            ax.set(xlabel='xyz'[a], ylabel='xyz'[b], title='Learned − FEM')
            fig.colorbar(errmesh, ax=ax, label='Signed joint-density error')
        m = entry['cpu_metrics']
        fig.suptitle(f"Law {entry['law']} · {entry['split']} · "
                     f"L1={m['l1']:.4f}, covariance error={100*m['relative_covariance_error']:.2f}%", fontsize=15)
        fig.text(.5, .002, 'Conservative learning-grid densities; full box; no invented trajectories. '
                 'White = recorded zero; black includes positive values below the colour floor. Linear signed error.',
                 ha='center', fontsize=9)
        fig.savefig(output / f"law{entry['law']}_density_comparison.png", dpi=145)
        plt.close(fig)
    # Same number of probability-weighted draws per panel; scale/density colours shared.
    fig = plt.figure(figsize=(17, 10), layout='constrained')
    vmax = max(float(p.max()) for data in fields for p in data.values())
    norm = LogNorm(1e-7, vmax)
    for row, (entry, data) in enumerate(zip(report['records'], fields)):
        for column, key in enumerate(('initial', 'target', 'learned')):
            p = data[key]
            rng = np.random.default_rng(report['rendering_seed'])
            probability = p.ravel() / p.sum()
            idx = rng.choice(p.size, size=14000, p=probability)
            cells = np.unravel_index(idx, shape)
            xyz = [edges[d][cells[d]] + widths[d]*rng.random(len(idx)) for d in range(3)]
            ax = fig.add_subplot(2, 3, row*3+column+1, projection='3d')
            points = ax.scatter(*xyz, c=p.ravel()[idx], s=1.7, alpha=.35, cmap='magma',
                                norm=norm, rasterized=True)
            ax.set(xlabel='x', ylabel='y', zlabel='z',
                   title=f"Law {entry['law']} · {entry['split']}\n{labels[column]}")
            for limits, setter in zip(BOUNDS, (ax.set_xlim, ax.set_ylim, ax.set_zlim)):
                setter(*limits)
            ax.view_init(24, -65)
    fig.colorbar(points, ax=fig.axes, shrink=.55, label='Voxel density (shared log scale)')
    fig.suptitle('Lorenz state-space distributions: archived inputs, FEM targets and checkpoint forecasts', fontsize=16)
    fig.text(.5, .003, 'Probability-weighted visualization draws from saved 3D voxel fields; '
             'these are not simulated particle paths or truth trajectories.', ha='center', fontsize=10)
    fig.savefig(output / 'state_space_comparison.png', dpi=145)
    plt.close(fig)
    report['figure_sha256'] = {p.name: sha(p) for p in output.glob('*.png')}
    report['matplotlib_version'] = matplotlib.__version__
    (output / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(output=str(output), figures=list(report['figure_sha256']))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('infer', 'render'))
    parser.add_argument('output', type=Path)
    parser.add_argument('--source', type=Path, default=ROOT/'runs/neural-pilot/20261004T133438Z')
    args = parser.parse_args()
    if args.stage == 'infer':
        infer(args.source, args.output)
    else:
        render(args.output)
