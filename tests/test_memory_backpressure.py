"""Memory scheduling must preserve live jobs rather than terminate them."""
import importlib.util
from pathlib import Path
import signal

spec = importlib.util.spec_from_file_location('memory_backpressure',
    Path(__file__).resolve().parents[1]/'mfem/memory_backpressure.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_pause_resume_hysteresis_without_termination():
    class Process:
        pid = 123
        returncode = None
        count = 0
        def poll(self):
            self.count += 1
            if self.count > 4:
                self.returncode = 0
            return self.returncode
    memory = iter([5,1,3,5])
    signals,updates = [],[]
    assert module.wait_with_backpressure(Process(),updates.append,
        read_memory=lambda: next(memory),send_signal=lambda pid,sig: signals.append(sig),
        sleep=lambda seconds: None,pause_kib=2,resume_kib=4) == 0
    assert signals == [signal.SIGSTOP,signal.SIGCONT]
    assert [item['paused'] for item in updates] == [False,True,True,False]


def test_resume_at_exact_two_gib_preserves_process():
    class Process:
        pid = 123
        returncode = None
        count = 0
        def poll(self):
            self.count += 1
            if self.count > 3:
                self.returncode = 0
            return self.returncode
    threshold = 2*1024*1024
    memory = iter([threshold-1, threshold, threshold+1])
    signals = []
    assert module.wait_with_backpressure(Process(), lambda update: None,
        read_memory=lambda: next(memory), send_signal=lambda pid,sig: signals.append(sig),
        sleep=lambda seconds: None) == 0
    assert signals == [signal.SIGSTOP, signal.SIGCONT]
