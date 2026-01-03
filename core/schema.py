from typing import Any, Mapping, TypedDict

EMPLOYMENT_STATUSES = ("employed", "unemployed", "student")
EDUCATION_LEVELS = ("high_school", "associate", "bachelor", "master", "phd", "other")
DIGITAL_LEVELS = ("weak", "medium", "good")
GOAL_TYPES = ("quick_income", "career_upgrade", "technical_switch")


class Profile(TypedDict):
    age: int
    employment_status: str
    education_level: str
    digital_level: str
    goal_type: str
    weekly_time_budget_hours: int


def _require(raw: Mapping[str, Any], key: str) -> Any:
    if key not in raw:
        raise ValueError(f"missing field: {key}")
    return raw[key]


def _validate_choice(value: str, options: tuple[str, ...], field: str) -> str:
    if value not in options:
        raise ValueError(f"invalid {field}: {value}")
    return value


def normalize_profile(raw: Mapping[str, Any]) -> Profile:
    age = int(_require(raw, "age"))
    if age < 0:
        raise ValueError("age must be non-negative")

    weekly_time_budget_hours = int(_require(raw, "weekly_time_budget_hours"))
    if weekly_time_budget_hours < 3 or weekly_time_budget_hours > 30:
        raise ValueError("weekly_time_budget_hours must be between 3 and 30")

    employment_status = _validate_choice(
        str(_require(raw, "employment_status")),
        EMPLOYMENT_STATUSES,
        "employment_status",
    )
    education_level = _validate_choice(
        str(_require(raw, "education_level")),
        EDUCATION_LEVELS,
        "education_level",
    )
    digital_level = _validate_choice(
        str(_require(raw, "digital_level")),
        DIGITAL_LEVELS,
        "digital_level",
    )
    goal_type = _validate_choice(
        str(_require(raw, "goal_type")),
        GOAL_TYPES,
        "goal_type",
    )

    return Profile(
        age=age,
        employment_status=employment_status,
        education_level=education_level,
        digital_level=digital_level,
        goal_type=goal_type,
        weekly_time_budget_hours=weekly_time_budget_hours,
    )
