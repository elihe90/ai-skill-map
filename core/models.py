from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    category: str
    description: str
    level: int
