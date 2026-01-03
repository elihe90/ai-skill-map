from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_users(path: Path = DEFAULT_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8-sig").strip()
        if not raw:
            return {}
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_users(users: Dict[str, Any], path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(users, ensure_ascii=True, indent=2)
    path.write_text(payload, encoding="utf-8")


def upsert_user_record(user_id: str, updates: Dict[str, Any], path: Path = DEFAULT_PATH) -> Dict[str, Any]:
    users = load_users(path)
    record = users.get(user_id, {})
    if not record:
        record = {"user_id": user_id, "created_at": _now_iso()}
    record.update(updates)
    record["updated_at"] = _now_iso()
    users[user_id] = record
    save_users(users, path)
    return record
