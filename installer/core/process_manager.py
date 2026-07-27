import psutil
import time
import sys

from typing import List, Set

from installer.core.models import BrowserProfile


def get_running_browser_pids(executables: List[str]) -> List[psutil.Process]:
    """Scans running processes and returns a list of psutil.Process matching target executables."""

    target_names = {exe.lower() for exe in executables}
    matching_processes: List[psutil.Process] = []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pname = proc.info['name']
            if pname and pname.lower() in target_names:
                matching_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return matching_processes


def terminate_browser_processes(profiles: List[BrowserProfile], timeout: float = 3.0) -> bool:
    """Finds all running processes for selected browser profiles and attempts to close their processes."""

    executables: Set[str] = set()

    for profile in profiles:
        executables.update(profile.executables)

    procs = get_running_browser_pids(list(executables))

    if not procs:
        return True

    # Attempt graceful shutdown first
    for proc in procs:
        try:
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    gone, alive = psutil.wait_procs(procs, timeout=timeout)

    # Force kill any remaining processes
    for proc in alive:
        try:
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return True
