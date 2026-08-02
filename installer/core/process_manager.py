import psutil
import time

from typing import List, Set

from core.models import BrowserProfile


def get_running_browser_pids(executables: List[str]) -> List[psutil.Process]:
    """Scans running processes and returns a list of psutil.Process matching target executables."""

    targets = {exe.lower() for exe in executables}
    matching_processes: List[psutil.Process] = []

    for proc in psutil.process_iter(['pid', 'exe']):
        try:
            pexe = proc.info.get('exe')

            if not pexe:
                continue

            pexe_lower = pexe.lower()

            if any(pexe_lower == target or pexe_lower.endswith(f"\\{target}") or pexe_lower.endswith(f"/{target}") for target in targets):
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

    for proc in procs:
        try:
            exe_path = proc.info.get('exe')

            if exe_path:
                for profile in profiles:
                    if not profile.executable_path:
                        pexe_lower = exe_path.lower()

                        if any(pexe_lower == target.lower() or pexe_lower.endswith(f"\\{target.lower()}") or pexe_lower.endswith(f"/{target.lower()}") for target in profile.executables):
                            profile.executable_path = exe_path

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Terminate captured processes
    for proc in procs:
        try:
            proc.terminate()

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    gone, alive = psutil.wait_procs(procs, timeout=timeout)

    for proc in alive:
        try:
            proc.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return True
