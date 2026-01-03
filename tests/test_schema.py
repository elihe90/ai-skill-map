import pytest

from core.schema import normalize_profile


def test_normalize_profile_success():
    raw = {
        "age": 27,
        "employment_status": "employed",
        "education_level": "bachelor",
        "digital_level": "medium",
        "goal_type": "career_upgrade",
        "weekly_time_budget_hours": 12,
    }
    profile = normalize_profile(raw)
    assert profile["age"] == 27
    assert profile["weekly_time_budget_hours"] == 12


def test_normalize_profile_invalid_goal():
    raw = {
        "age": 27,
        "employment_status": "employed",
        "education_level": "bachelor",
        "digital_level": "medium",
        "goal_type": "invalid",
        "weekly_time_budget_hours": 12,
    }
    with pytest.raises(ValueError):
        normalize_profile(raw)
