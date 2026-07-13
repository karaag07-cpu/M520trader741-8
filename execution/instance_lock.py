"""Single-instance guard so two bots can't run at once.

Running multiple bot processes means duplicate/conflicting orders (the cause of
the weekend crypto churn). On startup the bot writes its PID to ``bot.lock`` and
refuses to start if a *live* process already holds it. A stale lock (from a
crashed run) is detected via the PID no longer being alive and is reclaimed.
"""

from __future__ import annotations

import os
import subprocess

DEFAULT_LOCK_PATH = 'bot.lock'


def _pid_alive(pid):
    """Cross-platform check for whether a process id is currently running."""
    if pid <= 0:
        return False
    if os.name == 'nt':
        try:
            out = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                 capture_output=True, text=True)
            return str(pid) in out.stdout
        except Exception:
            return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True   # exists but not ours to signal
    except OSError:
        return False
    return True


def acquire(path=DEFAULT_LOCK_PATH):
    """Try to take the lock.

    Returns ``(ok, holder_pid)``. ``ok`` is False when another live instance
    already holds it (``holder_pid`` is that process). A stale lock is reclaimed.
    """
    if os.path.exists(path):
        try:
            existing = int(open(path).read().strip())
        except (ValueError, OSError):
            existing = -1
        if existing != os.getpid() and _pid_alive(existing):
            return False, existing
    try:
        with open(path, 'w') as fh:
            fh.write(str(os.getpid()))
    except OSError:
        pass  # best-effort; don't block startup on a write failure
    return True, os.getpid()


def release(path=DEFAULT_LOCK_PATH):
    """Remove the lock if we own it."""
    try:
        if os.path.exists(path) and int(open(path).read().strip()) == os.getpid():
            os.remove(path)
    except (ValueError, OSError):
        pass
