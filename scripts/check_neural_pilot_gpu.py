"""Hardware/software smoke test; random fixtures are not scientific datasets."""
import importlib.util
import json
from pathlib import Path
import tempfile

import torch


def main():
    source=Path(__file__).with_name('train_neural_pilot.py')
    spec=importlib.util.spec_from_file_location('pilot_gpu_check',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable: hardware test cannot pass')
    torch.manual_seed(71023)
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    model=module.Operator().cuda()
    x=torch.rand(1,1,60,72,72,device='cuda')
    target=torch.ones_like(x)
    optimizer=torch.optim.Adam(model.parameters(),lr=.002)
    for _ in range(2):
        optimizer.zero_grad()
        prediction=model(x)
        loss=(prediction-target).square().mean()
        loss.backward()
        assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
        optimizer.step()
    with torch.no_grad():
        prediction=model(x)
        assert torch.isfinite(prediction).all() and prediction.min()>=0
        assert abs(prediction.mean().item()-1)<1e-6
        report=module.metrics(prediction,target)
        cpu=module.Operator().cpu()
        cpu.load_state_dict({k:v.cpu() for k,v in model.state_dict().items()})
        cpu_prediction=cpu(x.cpu())
        torch.testing.assert_close(prediction.cpu(),cpu_prediction,rtol=1e-4,atol=1e-5)
    with tempfile.TemporaryDirectory(prefix='lorenz-cuda-check-') as directory:
        checkpoint=Path(directory)/'model.pt'
        torch.save(dict(model=model.state_dict()),checkpoint)
        restored=module.Operator().cuda()
        restored.load_state_dict(torch.load(checkpoint,weights_only=True,map_location='cuda')['model'])
        with torch.no_grad():
            torch.testing.assert_close(restored(x),prediction)
    torch.cuda.synchronize()
    print(json.dumps(dict(passed=True,fixture='random software test only',torch=torch.__version__,cuda_runtime=torch.version.cuda,gpu=torch.cuda.get_device_name(0),peak_allocated_MiB=torch.cuda.max_memory_allocated()/1024**2,metrics=report),indent=2))


if __name__=='__main__':
    main()
