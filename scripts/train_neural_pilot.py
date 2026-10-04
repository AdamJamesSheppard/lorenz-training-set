"""GPU-preferred 3D spectral operator for accepted conservative density pairs."""
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F


class Spectral(nn.Module):
    def __init__(self, width=8, modes=4):
        super().__init__()
        self.modes = modes
        self.weights = nn.Parameter(torch.randn(4, width, width, modes, modes, modes, dtype=torch.cfloat)/width)

    def forward(self, x):
        spectrum = torch.fft.rfftn(x, dim=(-3, -2, -1))
        out = torch.zeros_like(spectrum)
        m = self.modes
        for i, (a, b) in enumerate(((slice(0,m),slice(0,m)), (slice(-m,None),slice(0,m)), (slice(0,m),slice(-m,None)), (slice(-m,None),slice(-m,None)))):
            out[:, :, a, b, :m] = torch.einsum('bixyz,ioxyz->boxyz', spectrum[:, :, a, b, :m], self.weights[i])
        return torch.fft.irfftn(out, s=x.shape[-3:], dim=(-3,-2,-1))


class Operator(nn.Module):
    def __init__(self):
        super().__init__()
        self.lift = nn.Conv3d(4, 8, 1)
        self.spectral = nn.ModuleList([Spectral() for _ in range(2)])
        self.local = nn.ModuleList([nn.Conv3d(8, 8, 1) for _ in range(2)])
        self.head = nn.Conv3d(8, 1, 1)
        nn.init.zeros_(self.head.weight)
        nn.init.constant_(self.head.bias, -.2)

    def forward(self, density):
        axes = [torch.linspace(-1,1,n,device=density.device) for n in density.shape[-3:]]
        coordinates = torch.stack(torch.meshgrid(*axes,indexing='ij'))[None].expand(density.shape[0],-1,-1,-1,-1)
        x = self.lift(torch.cat([density,coordinates],dim=1))
        # Zero padding reduces wraparound; reflecting physics resides in targets.
        x = F.pad(x,(0,4,0,4,0,4))
        for spectral, local in zip(self.spectral,self.local):
            x = F.gelu(spectral(x)+local(x))
        x = self.head(x)[:, :, :-4, :-4, :-4]
        # Start near persistence, then learn a density-level forecast correction.
        positive = F.softplus(density+x, beta=20)
        return positive/positive.mean(dim=(-3,-2,-1),keepdim=True)


def metrics(prediction, target):
    p, q = prediction.detach().double().cpu().numpy().ravel(), target.detach().double().cpu().numpy().ravel()
    shape = prediction.shape[-3:]
    def statistics(field):
        probability = field.reshape(shape)/field.sum()
        coordinates = np.meshgrid(*[np.linspace(a+(b-a)/(2*n), b-(b-a)/(2*n), n) for a,b,n in zip((-30,-40,-10),(30,40,70),shape)], indexing='ij')
        means = np.array([(probability*x).sum() for x in coordinates])
        covariance = np.array([[(probability*(x-means[i])*(y-means[j])).sum() for j,y in enumerate(coordinates)] for i,x in enumerate(coordinates)])
        marginals = [probability.sum(axis=tuple(j for j in range(3) if j!=i)) for i in range(3)]
        return means,covariance,marginals
    mean,cov,marginals = statistics(p)
    target_mean,target_cov,target_marginals = statistics(q)
    return dict(l1=float(np.abs(p-q).mean()), relative_l2=float(np.linalg.norm(p-q)/np.linalg.norm(q)), mass_error=float(abs(p.mean()-1)), negative_mass=float(-p[p<0].sum()/p.size), mean_error=float(np.linalg.norm(mean-target_mean)), relative_covariance_error=float(np.linalg.norm(cov-target_cov)/np.linalg.norm(target_cov)), marginal_tv=[float(.5*np.abs(a-b).sum()) for a,b in zip(marginals,target_marginals)])


def main(root):
    config = json.loads((root/'config.json').read_text())
    torch.manual_seed(config['seed'])
    torch.set_num_threads(4)
    requested = config.get('device', 'auto')
    device = torch.device('cuda' if requested == 'auto' and torch.cuda.is_available() else 'cpu' if requested == 'auto' else requested)
    if device.type == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA explicitly requested but unavailable')
    # Record actual execution; preserve CPU fallback when auto finds no CUDA.
    hardware = dict(device=str(device), torch_version=torch.__version__, cuda_runtime=torch.version.cuda,
                    gpu_name=torch.cuda.get_device_name(device) if device.type == 'cuda' else None)
    if device.type == 'cuda':
        hardware['compute_capability'] = torch.cuda.get_device_capability(device)
        hardware['total_device_memory_bytes'] = torch.cuda.get_device_properties(device).total_memory
    (root/'training_device.json').write_text(json.dumps(hardware, indent=2))
    print(hardware, flush=True)
    pairs = []
    for entry in json.loads((root/'manifest.json').read_text()):
        data = np.load(root/entry['path'])
        # Mean-one scaling: density = network field / physical box volume.
        pairs.append((entry['split'],*[torch.from_numpy(data[k]*384000)[None,None].to(device) for k in ('initial','final')]))
    model = Operator().to(device)
    optimizer = torch.optim.Adam(model.parameters(),lr=.002)
    best = float('inf')
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    start = time.monotonic()
    history = []
    for epoch in range(config['epochs']):
        model.train()
        losses = []
        for split, x, y in pairs:
            if split != 'train':
                continue
            optimizer.zero_grad()
            prediction = model(x)
            loss = (prediction-y).square().mean()/y.square().mean()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            validation = np.mean([((model(x)-y).square().mean()/y.square().mean()).item() for split,x,y in pairs if split=='validation'])
        if validation < best:
            best = validation
            torch.save(dict(model=model.state_dict(),epoch=epoch,config=config),root/'best_model.pt')
        history.append(dict(epoch=epoch,training=float(np.mean(losses)),validation=validation))
        (root/'training_history.json').write_text(json.dumps(history))
        print(history[-1],flush=True)
    model.load_state_dict(torch.load(root/'best_model.pt',weights_only=True,map_location=device)['model'])
    results = []
    with torch.no_grad():
        for split,x,y in pairs:
            predicted = model(x)
            results.append(dict(split=split,operator=metrics(predicted,y),persistence=metrics(x,y)))
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
        hardware['peak_allocated_bytes'] = torch.cuda.max_memory_allocated(device)
        hardware['peak_reserved_bytes'] = torch.cuda.max_memory_reserved(device)
    (root/'evaluation.json').write_text(json.dumps(dict(scope=config['scope'],results=results,runtime_seconds=time.monotonic()-start,hardware=hardware,production_authorized=False),indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
