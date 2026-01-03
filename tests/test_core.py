import json

from core.loader import load_skills, parse_skill
from core.models import Skill
from core.service import filter_skills, list_categories, skill_level_label


def test_parse_skill_casts_fields():
    item = {
        "id": 10,
        "name": "Skill",
        "category": "Cat",
        "description": "Desc",
        "level": "2",
    }
    skill = parse_skill(item)
    assert skill == Skill(
        id="10",
        name="Skill",
        category="Cat",
        description="Desc",
        level=2,
    )


def test_load_skills_from_json(tmp_path):
    path = tmp_path / "skills.json"
    payload = [
        {
            "id": "one",
            "name": "Alpha",
            "category": "ML",
            "description": "Basics",
            "level": 1,
        },
        {
            "id": "two",
            "name": "Beta",
            "category": "Data",
            "description": "Pipelines",
            "level": 3,
        },
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")
    skills = load_skills(path)
    assert len(skills) == 2
    assert skills[0].name == "Alpha"


def test_list_categories_sorted():
    skills = [
        Skill(id="1", name="A", category="B", description="", level=1),
        Skill(id="2", name="C", category="A", description="", level=1),
    ]
    assert list_categories(skills) == ["A", "B"]


def test_filter_skills_query_category_level():
    skills = [
        Skill(id="1", name="Alpha", category="ML", description="First", level=2),
        Skill(id="2", name="Beta", category="Data", description="Second", level=4),
    ]
    filtered = filter_skills(skills, query="alpha", category="ML", min_level=1)
    assert [skill.id for skill in filtered] == ["1"]

    filtered = filter_skills(skills, query="", category=None, min_level=3)
    assert [skill.id for skill in filtered] == ["2"]


def test_skill_level_label_unknown():
    assert skill_level_label(99) == "نامشخص"
