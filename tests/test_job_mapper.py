from core.job_mapper import map_jobs_from_gap


def _gap(training_level, courses, scores, blocked=None):
    payload = {
        "training_level": training_level,
        "recommended_courses": courses,
        "interview_scores": scores,
    }
    if blocked is not None:
        payload["blocked_courses"] = blocked
    return payload


def test_level_a_content_or_operator():
    scores = {
        "execution": 2,
        "problem_solving": 2,
        "learning": 2,
        "planning": 1,
        "ai_mindset": 2,
    }
    gap = _gap("A", ["3512100030", "3512100023", "2166100024"], scores)
    result = map_jobs_from_gap(gap, top_k=5)
    titles = {job["title_fa"] for job in result["reachable_jobs"]}
    assert (
        "کارشناس تولید محتوا با هوش مصنوعی" in titles
        or "اپراتور ابزارهای هوش مصنوعی" in titles
    )


def test_level_a_no_level_c_titles():
    scores = {"execution": 1, "problem_solving": 1, "learning": 1, "planning": 1, "ai_mindset": 1}
    gap = _gap("A", ["3512100030", "3512100023"], scores)
    result = map_jobs_from_gap(gap, top_k=5)
    for job in result["reachable_jobs"]:
        assert job["level"] != "C"


def test_level_b_python_system_problem_solving():
    scores = {"execution": 3, "problem_solving": 3, "learning": 3, "planning": 3, "ai_mindset": 3}
    gap = _gap("B", ["2511200021", "2511200020", "2511200005"], scores)
    result = map_jobs_from_gap(gap, top_k=6)
    assert any(job["level"] == "B" for job in result["reachable_jobs"])


def test_level_c_ml_specialist_reachable():
    scores = {"execution": 4, "problem_solving": 4, "learning": 4, "planning": 3, "ai_mindset": 4}
    gap = _gap("C", ["2511200021", "2511200022", "2511200005"], scores)
    result = map_jobs_from_gap(gap, top_k=6)
    titles = {job["title_fa"] for job in result["reachable_jobs"]}
    assert "متخصص یادگیری ماشین" in titles


def test_blocked_courses_excluded_from_next_codes():
    scores = {"execution": 3, "problem_solving": 3, "learning": 3, "planning": 3, "ai_mindset": 3}
    gap = _gap(
        "A",
        ["3512100030"],
        scores,
        blocked=["2166100024"],
    )
    result = map_jobs_from_gap(gap, top_k=3)
    for job in result["reachable_jobs"]:
        assert "2166100024" not in job["next_courses_to_unlock"]


def test_match_score_bounds_and_missing_dedup():
    scores = {"execution": 2, "problem_solving": 2, "learning": 2, "planning": 2, "ai_mindset": 2}
    gap = _gap("A", ["3512100030"], scores)
    result = map_jobs_from_gap(gap, top_k=5)
    for job in result["reachable_jobs"]:
        assert 0 <= job["match_score"] <= 100
        missing = job["missing_courses"]
        assert len(missing) == len(set(missing))


def test_satisfied_course_in_why():
    scores = {"execution": 2, "problem_solving": 2, "learning": 2, "planning": 1, "ai_mindset": 2}
    gap = _gap("A", ["3512100030", "2166100024"], scores)
    result = map_jobs_from_gap(gap, top_k=5)
    job = next((item for item in result["reachable_jobs"] if item["job_id"] == "J-A-01"), None)
    assert job is not None
    assert any("3512100030" in reason for reason in job.get("why_fa", []))

