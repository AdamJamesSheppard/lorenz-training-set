"""Pause/resume a local MPI process group under temporary memory pressure."""
import os
import signal
import time
from pathlib import Path


def available_kib():
    return int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                    if line.startswith('MemAvailable:')))


def wait_with_backpressure(process, update, read_memory=available_kib,
                           send_signal=os.killpg, sleep=time.sleep,
                           pause_kib=2*1024*1024, resume_kib=4*1024*1024):
    """Keep allocations alive; wait indefinitely for external RAM recovery.

    Requires Popen(start_new_session=True). Hysteresis prevents rapid cycling.
    This is scheduling backpressure, not out-of-core matrix storage. It does
    not protect against the kernel OOM killer or allocations between polls.
    """
    if resume_kib <= pause_kib:
        raise ValueError('Resume threshold must exceed pause threshold')
    paused = False
    minimum = None
    while process.poll() is None:
        available = read_memory()
        minimum = available if minimum is None else min(minimum, available)
        try:
            if not paused and available < pause_kib:
                send_signal(process.pid, signal.SIGSTOP)
                paused = True
            elif paused and available >= resume_kib:
                send_signal(process.pid, signal.SIGCONT)
                paused = False
        except ProcessLookupError:
            if process.poll() is None:
                raise
            break
        update(dict(available_kib=available, minimum_available_kib=minimum,
                    pause_threshold_kib=pause_kib, resume_threshold_kib=resume_kib,
                    paused=paused, process_group=process.pid))
        sleep(5)
    return process.returncode
