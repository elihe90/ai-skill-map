from typing import List, Optional, Sequence

from .models import Skill


_LEVEL_LABELS = {
    1: "مبتدی",
    2: "پایه",
    3: "میانی",
    4: "پیشرفته",
    5: "خبره",
}


def skill_level_label(level: int) -> str:
    return _LEVEL_LABELS.get(level, "نامشخص")


def list_categories(skills: Sequence[Skill]) -> List[str]:
    return sorted({skill.category for skill in skills})


def filter_skills(
    skills: Sequence[Skill],
    query: str,
    category: Optional[str],
    min_level: int,
) -> List[Skill]:
    normalized_query = query.strip().lower()
    results: List[Skill] = []
    for skill in skills:
        if category and skill.category != category:
            continue
        if skill.level < min_level:
            continue
        if normalized_query:
            haystack = f"{skill.name} {skill.description} {skill.category}".lower()
            if normalized_query not in haystack:
                continue
        results.append(skill)
    return results
