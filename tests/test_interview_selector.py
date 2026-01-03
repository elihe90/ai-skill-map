from core.interview_selector import load_question_bank, select_questions


def _count_tag(questions, tag):
    return sum(1 for question in questions if tag in question.get("tags", []))


def _count_difficulty(questions, difficulty):
    return sum(1 for question in questions if question.get("difficulty") == difficulty)


def _has_tag(questions, tag):
    return _count_tag(questions, tag) > 0


def _has_problem_or_learning(questions):
    return _has_tag(questions, "problem_solving") or _has_tag(questions, "learning")


def _unique_ids(questions):
    ids = [question.get("id") for question in questions]
    return len(ids) == len(set(ids))


def test_select_questions_weak_digital_quick_income():
    bank = load_question_bank()
    profile = {"digital_level": "ضعیف", "goal": "درآمد سریع"}
    selected = select_questions(profile, bank, n=5, seed=42)

    assert len(selected) == 5
    assert _unique_ids(selected)
    assert _count_tag(selected, "digital") >= 2
    assert _count_tag(selected, "execution") >= 2
    assert _count_difficulty(selected, "easy") >= 2
    assert _has_problem_or_learning(selected)


def test_select_questions_good_digital_technical_switch():
    bank = load_question_bank()
    profile = {"digital_level": "خوب", "goal": "تغییر مسیر فنی"}
    selected = select_questions(profile, bank, n=5, seed=42)

    assert len(selected) == 5
    assert _unique_ids(selected)
    assert _count_tag(selected, "digital") >= 1
    assert _count_tag(selected, "execution") >= 1
    assert _count_tag(selected, "learning") >= 1
    assert _count_tag(selected, "problem_solving") >= 1


def test_select_questions_medium_digital_career_upgrade():
    bank = load_question_bank()
    profile = {"digital_level": "متوسط", "goal": "ارتقای شغلی"}
    selected = select_questions(profile, bank, n=5, seed=42)

    assert len(selected) == 5
    assert _unique_ids(selected)
    assert _count_tag(selected, "digital") >= 1
    assert _count_tag(selected, "execution") >= 1
    assert _has_problem_or_learning(selected)
    assert _count_tag(selected, "planning") + _count_tag(selected, "quality") >= 1


def test_select_questions_missing_profile():
    bank = load_question_bank()
    selected = select_questions({}, bank, n=5, seed=42)

    assert len(selected) == 5
    assert _unique_ids(selected)
    assert _count_tag(selected, "digital") >= 1
    assert _count_tag(selected, "execution") >= 1
    assert _has_problem_or_learning(selected)
