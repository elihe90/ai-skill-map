import json
from pathlib import Path
from typing import List

from .models import Skill


def load_skills(path: Path) -> List[Skill]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("skills data must be a list")
    return [parse_skill(item) for item in data]


def parse_skill(item: dict) -> Skill:
    required = ["id", "name", "category", "description", "level"]
    missing = [key for key in required if key not in item]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    return Skill(
        id=str(item["id"]),
        name=str(item["name"]),
        category=str(item["category"]),
        description=str(item["description"]),
        level=int(item["level"]),
    )
