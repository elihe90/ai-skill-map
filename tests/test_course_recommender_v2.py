from core.course_recommender_v2 import recommend_courses


def test_course_recommender_v2_a_content():
    result = recommend_courses("A", "content", weekly_time=None, goal=None)
    courses = result["recommended_courses"]
    assert "3512100030" in courses
    assert "2166100024" in courses
    assert "2166100025" in courses
    assert "3512100023" in courses


def test_course_recommender_v2_low_time_limits_courses():
    result = recommend_courses("A", "automation", weekly_time="1-2", goal=None)
    assert len(result["recommended_courses"]) <= 3


def test_course_recommender_v2_goal_affects_ordering():
    result = recommend_courses("A", "content", weekly_time=None, goal="????? ????")
    courses = result["recommended_courses"]
    assert courses[0] in {"2166100024", "2166100025", "3512100023", "3512100030"}
