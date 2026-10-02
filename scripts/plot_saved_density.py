#!/usr/bin/env python3
"""Render archived conservative density averages, without a solver run."""
import argparse
import hashlib
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BOUNDS = [(-30., 30.), (-40., 40.), (-10., 70.)]
SHAPE = (180, 216, 216)


def render(p, edges, title, time):
    widths = [np.diff(e) for e in edges]
    mass = p * widths[0][:, None, None] * widths[1][None, :, None] * widths[2][None, None, :]
    rng = np.random.default_rng(1963)
    idx = np.searchsorted(np.cumsum(np.maximum(mass, 0).ravel()) / np.maximum(mass, 0).sum(), rng.random(18000))
    cells = np.unravel_index(idx, p.shape)
    xyz = [edges[d][cells[d]] + widths[d][cells[d]] * rng.random(len(idx)) for d in range(3)]
    fig = plt.figure(figsize=(12, 9), layout='constrained')
    ax = fig.add_subplot(221, projection='3d')
    ax.scatter(*xyz, c=np.where(xyz[0] >= 0, '#e56b6f', '#247ba0'), s=1, alpha=.12, rasterized=True)
    for d, setter in enumerate((ax.set_xlim, ax.set_ylim, ax.set_zlim)):
        setter(*BOUNDS[d])
    ax.set(xlabel='x', ylabel='y', zlabel='z', title='Full state-space box: density visualization samples')
    ax.view_init(22, -60)
    for panel, (a, b, integrated) in enumerate(((0, 1, 2), (0, 2, 1), (1, 2, 0)), 2):
        ax = fig.add_subplot(2, 2, panel)
        weight_shape = [1, 1, 1]
        weight_shape[integrated] = len(widths[integrated])
        marginal = (p * widths[integrated].reshape(weight_shape)).sum(axis=integrated)
        im = ax.pcolormesh(edges[a], edges[b], np.ma.masked_less_equal(marginal.T, 0), norm=LogNorm(1e-6, .1), cmap='magma', shading='flat')
        ax.set(xlabel='xyz'[a], ylabel='xyz'[b], title=f'Integrated {"xyz"[a]}–{"xyz"[b]} marginal (full box)')
        fig.colorbar(im, ax=ax, label='Probability density')
    fig.suptitle(f'{title}\nt = {time:.4f} · integrated mass = {mass.sum():.12f}', fontsize=14)
    fig.text(.5, .002, 'Saved 3D conservative cell averages. Fixed scales; no time interpolation. Cloud samples visualize density, not particle trajectories.', ha='center', fontsize=9)
    stream = io.BytesIO()
    fig.savefig(stream, format='png', dpi=125)
    plt.close(fig)
    return Image.open(stream).convert('RGB'), float(mass.sum()), float(-mass[p < 0].sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    uniform = [np.linspace(lo, hi, n + 1) for (lo, hi), n in zip(BOUNDS, SHAPE)]
    latest = ROOT / 'runs/mfem-support-depth/20261001T224713Z/mfem'
    frames = []
    for name, time in [('initial', 0.), ('final', .05)]:
        source = latest / f'{name}_q2_subcell_averages.bin'
        p = np.fromfile(source, dtype=np.float64).reshape(SHAPE)
        frame, mass, negative = render(p, uniform, 'Latest MFEM run · only initial and final fields archived', time)
        frame.save(args.output / f'latest_{name}.png')
        frames.append(frame)
        records.append(dict(source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), time=time, mass=mass, negative_mass=negative, shape=list(p.shape)))
    frames[0].save(args.output / 'latest_endpoints.gif', save_all=True, append_images=frames[1:], duration=1800, loop=0)
    axes = json.loads((ROOT / 'experiments/mature-graded-fine-axes.json').read_text())
    graded = [lo + np.array(axes['edge_indices'][axis]) / n * (hi - lo) for axis, n, (lo, hi) in zip('xyz', SHAPE, BOUNDS)]
    frames = []
    snapshots = ROOT / 'runs/mature-time-aggregated-grid-pipeline/20260915T134916Z/indicator_snapshots'
    for source in sorted(snapshots.glob('indicator_step_*.npz')):
        with np.load(source) as data:
            p = data['cell_average']
            expected = np.diff(graded[0])[:, None, None] * np.diff(graded[1])[None, :, None] * np.diff(graded[2])[None, None, :]
            np.testing.assert_allclose(expected, data['cell_volume'], rtol=1e-10, atol=1e-12)
            time = float(data['time'])
            frame, mass, negative = render(p, graded, 'Earlier DOLFINx fine-graded reference · saved time sequence', time)
        frames.append(frame)
        records.append(dict(source=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), time=time, mass=mass, negative_mass=negative, shape=list(p.shape)))
    if len(frames) != 11:
        raise RuntimeError(f'Expected 11 reference snapshots, found {len(frames)}')
    frames[0].save(args.output / 'reference_evolution.gif', save_all=True, append_images=frames[1:], duration=900, loop=0)
    manifest = dict(description='Actual saved full 3D conservative averages; reference trajectory is distinct from latest MFEM endpoints.', bounds=BOUNDS, rendering_seed=1963, temporal_interpolation=False, records=records)
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(output=str(args.output), records=len(records), mass_range=[min(r['mass'] for r in records), max(r['mass'] for r in records)], max_negative_mass=max(r['negative_mass'] for r in records))))


if __name__ == '__main__':
    main()
