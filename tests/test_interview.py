from core.interview import score_interview


def test_score_interview_bounds():
    answers = [
        "برای حل مسئله ابتدا تحلیل می کنم و راهکار می دهم.",
        "برنامه اجرا و زمان بندی و تمرین یادگیری را مشخص می کنم.",
    ]
    scores = score_interview(answers)
    assert set(scores.keys()) == {
        "problem_solving_score",
        "execution_score",
        "ai_mindset_score",
        "learning_score",
        "planning_score",
    }
    for value in scores.values():
        assert 0 <= value <= 5
