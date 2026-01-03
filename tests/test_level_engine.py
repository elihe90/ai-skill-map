from core.level_engine import determine_levels


def test_special_case_high_learning_low_execution():
    scores = {
        "learning": 5,
        "planning": 4,
        "ai_mindset": 5,
        "execution": 1,
        "problem_solving": 1,
    }
    levels = determine_levels(scores, track=None)
    assert levels["training_level"] == "B"
    assert levels["readiness_level"] == "A"


def test_low_learning_maps_to_a():
    scores = {
        "learning": 1,
        "planning": 1,
        "ai_mindset": 2,
        "execution": 4,
        "problem_solving": 4,
    }
    levels = determine_levels(scores, track=None)
    assert levels["training_level"] == "A"


def test_all_high_maps_to_c():
    scores = {
        "learning": 5,
        "planning": 5,
        "ai_mindset": 4,
        "execution": 4,
        "problem_solving": 5,
    }
    levels = determine_levels(scores, track=None)
    assert levels["training_level"] == "C"
    assert levels["readiness_level"] == "C"
