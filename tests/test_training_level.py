from core.training_level import determine_training_level


def test_training_level_very_weak():
    profile = {"goal": "درآمد سریع", "digital_level": "متوسط"}
    scores = {
        "execution": 1,
        "problem_solving": 1,
        "learning": 3,
        "planning": 2,
        "ai_mindset": 1,
    }
    result = determine_training_level(profile, scores)
    assert result["training_level"] == "A"
    assert len(result["reason_fa"]) >= 2


def test_training_level_medium_balanced():
    profile = {"goal": "ارتقای شغلی", "digital_level": "متوسط"}
    scores = {
        "execution": 3,
        "problem_solving": 3,
        "learning": 3,
        "planning": 3,
        "ai_mindset": 3,
    }
    result = determine_training_level(profile, scores)
    assert result["training_level"] == "B"
    assert len(result["reason_fa"]) >= 2


def test_training_level_strong_technical_goal():
    profile = {"goal": "تغییر مسیر فنی", "digital_level": "خوب"}
    scores = {
        "execution": 4,
        "problem_solving": 4,
        "learning": 4,
        "planning": 3,
        "ai_mindset": 4,
    }
    result = determine_training_level(profile, scores)
    assert result["training_level"] == "C"
    assert len(result["reason_fa"]) >= 2


def test_training_level_strong_non_technical_goal():
    profile = {"goal": "ارتقای شغلی", "digital_level": "خوب"}
    scores = {
        "execution": 4,
        "problem_solving": 4,
        "learning": 4,
        "planning": 3,
        "ai_mindset": 4,
    }
    result = determine_training_level(profile, scores)
    assert result["training_level"] == "B"
    assert len(result["reason_fa"]) >= 2


def test_training_level_weak_digital():
    profile = {"goal": "تغییر مسیر فنی", "digital_level": "ضعیف"}
    scores = {
        "execution": 4,
        "problem_solving": 4,
        "learning": 5,
        "planning": 4,
        "ai_mindset": 4,
    }
    result = determine_training_level(profile, scores)
    assert result["training_level"] == "A"
    assert len(result["reason_fa"]) >= 2
