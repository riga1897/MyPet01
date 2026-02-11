"""File utilities for tests with Windows compatibility."""
import contextlib
import gc
import os
import shutil
import stat
import time
from typing import Any


def _remove_readonly(func: Any, path: str, excinfo: Any) -> None:
    """Error handler for shutil.rmtree on Windows.
    
    Windows often locks files that are still open. This handler:
    1. Forces garbage collection to close file handles
    2. Removes read-only flag
    3. Retries the operation
    """
    gc.collect()
    time.sleep(0.1)
    os.chmod(path, stat.S_IWRITE)
    with contextlib.suppress(PermissionError):
        func(path)


def safe_remove_file(path: str, retries: int = 5) -> None:
    """Safely remove a file with retries for Windows compatibility.
    
    Args:
        path: Path to file to remove
        retries: Number of retry attempts (default 5)
    """
    for i in range(retries):
        try:
            gc.collect()
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
            return
        except PermissionError:
            if i < retries - 1:
                time.sleep(0.2 * (i + 1))


def safe_rmtree(path: str, retries: int = 3) -> None:
    """Safely remove a directory tree with retries for Windows compatibility.
    
    Args:
        path: Path to directory to remove
        retries: Number of retry attempts (default 3)
    """
    for i in range(retries):
        try:
            gc.collect()
            time.sleep(0.1)
            if os.path.exists(path):
                shutil.rmtree(path, onerror=_remove_readonly)
            return
        except PermissionError:
            if i < retries - 1:
                time.sleep(0.5 * (i + 1))
