import os
from pathlib import Path
from typing import Optional


_LOADED = False


def load_env(path: str = ".env") -> None:
    """Load environment variables from a simple .env file if present."""
    global _LOADED
    if _LOADED:
        return

    file_path = Path(path)
    if not file_path.exists():
        _LOADED = True
        return

    lines = file_path.read_text(encoding="utf-8").splitlines()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if not key or value == "":
            continue
        if key not in os.environ:
            os.environ[key] = value

    _LOADED = True


def _strip_quotes(value: str) -> str:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value
