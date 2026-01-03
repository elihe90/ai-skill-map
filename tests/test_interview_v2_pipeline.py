from core.course_recommender_v2 import recommend_courses
from core.track_selector import select_track


def test_gap_has_recommended_courses_not_empty():
    track_info = select_track(
        "درآمد سریع",
        "۳–۵ ساعت",
        "تولید محتوا و شبکه‌های اجتماعی",
    )
    payload = recommend_courses("A", track_info["track"], "??? ????", "????? ????")
    gap = {
        "training_level": "A",
        "interview_scores": {
            "execution": 2,
            "problem_solving": 2,
            "learning": 2,
            "planning": 1,
            "ai_mindset": 2,
        },
        "recommended_courses": payload["recommended_courses"],
    }
    assert gap["recommended_courses"]
