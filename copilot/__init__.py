"""Live sales-call copilot powered by TypeSafe Jev (System One)."""

import os as _os
import sys as _sys
from pathlib import Path as _Path


def _load_dotenv(path: _Path = _Path(__file__).resolve().parent.parent / ".env") -> None:
    """KEY=value lines from the project's .env, without overriding variables already set (no dependency needed)."""
    if not path.is_file() or "pytest" in _sys.modules:  # tests stay offline unless keys are exported explicitly
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        _os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()
