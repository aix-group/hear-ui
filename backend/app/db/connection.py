"""Compatibility shim.

This project has a package `app/db/` (directory) which contains `base.py` and
other DB helpers. Older code also placed a module `app/connection.py` which shadows
the package and breaks imports like `from app.db.base import SQLModel`.

To remain backward compatible without deleting files during runtime we load
the real package module `app/db/base.py` from its file location and inject it
into `sys.modules` as `app.db.base`. This allows Alembic and other code to
import `app.db.base` even when this shim module is present.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Path to the real package module file (app/db/base.py)
base_file = Path(__file__).resolve().parent / "db" / "base.py"

spec = importlib.util.spec_from_file_location("app.db.base", str(base_file))
module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
# Execute the module in its own namespace
spec.loader.exec_module(module)  # type: ignore[attr-defined, union-attr]

# Register the loaded module under the expected name so `from app.db.base`
# works even though this file exists.
sys.modules["app.db.base"] = module

# Expose the module as attribute for direct access if any code does
# `import app.db; app.db.base`
base = module
