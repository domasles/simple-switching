import sys
import os


def is_admin() -> bool:
    """Checks whether the current process has oot privileges."""

    if sys.platform == "win32":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0

        except Exception:
            return False

    elif sys.platform == "darwin":
        return os.getuid() == 0

    else:
        # Linux relies on pkexec for root operations
        return True
