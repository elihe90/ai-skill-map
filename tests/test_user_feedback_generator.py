import json

from core.user_feedback_generator import generate_user_feedback

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None


class FakeAvalAIClient:
    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.model = "gpt-4o-mini"

    def chat_completions(self, payload):
        self.calls += 1
        return {"choices": [{"message": {"content": json.dumps(self.response, ensure_ascii=False)}}]}


class FailingAvalAIClient:
    def __init__(self):
        self.model = "gpt-4o-mini"

    def chat_completions(self, payload):
        raise RuntimeError("boom")


def _reset_cache():
    if st is not None:
        st.session_state["user_feedback_cache"] = {}


def _sample_inputs():
    gap = {
        "training_level": "A",
        "track": "content",
        "interview_scores": {
            "execution": 2,
            "problem_solving": 2,
            "learning": 2,
            "planning": 1,
            "ai_mindset": 2,
        },
        "recommended_courses": ["3512100030", "2166100024"],
    }
    interview_questions = [
        {"id": "CORE_Q1", "text_fa": "سوال ۱", "answer_type": "checkbox+text"},
        {"id": "CORE_Q2", "text_fa": "سوال ۲", "answer_type": "text"},
    ]
    interview_answers = {
        "CORE_Q1": {"choices": ["گزینه ۱"], "text": "توضیح کوتاه"},
        "CORE_Q2": {"text": "پاسخ نمونه"},
    }
    job_mapping = {
        "reachable_jobs": [{"title_fa": "شغل الف"}, {"title_fa": "شغل ب"}],
        "next_level_jobs": [{"title_fa": "شغل ج", "unlock_with": ["2511200021"]}],
    }
    course_catalog = {
        "3512100030": {"title_fa": "مبانی هوش مصنوعی"},
        "2166100024": {"title_fa": "تولید محتوای متنی"},
    }
    return gap, interview_questions, interview_answers, job_mapping, course_catalog


def test_generate_user_feedback_valid_and_cached():
    _reset_cache()
    gap, questions, answers, jobs, catalog = _sample_inputs()
    response = {
        "summary_fa": "خلاصه کوتاه وضعیت.",
        "strengths_fa": ["نقطه قوت ۱"],
        "gaps_fa": ["شکاف ۱"],
        "next_actions_fa": [
            {"title": "این هفته", "timeframe": "۷ روز", "steps": ["کار ۱"]}
        ],
        "course_plan_fa": [
            {
                "phase": "شروع سریع",
                "courses": [
                    {
                        "code": "3512100030",
                        "title": "مبانی هوش مصنوعی",
                        "why": "دلیل",
                    }
                ],
            }
        ],
        "job_path_fa": {
            "target_job": {"title": "شغل الف", "why_fit": "تناسب"},
            "reachable_now": [{"title": "شغل الف", "why": "دلیل"}],
            "next_level": [{"title": "شغل ج", "unlock_with": ["2511200021"]}],
        },
        "warnings_fa": [],
    }
    client = FakeAvalAIClient(response)
    report = generate_user_feedback(gap, questions, answers, jobs, catalog, client)
    assert report["summary_fa"]
    assert client.calls == 1

    report_again = generate_user_feedback(gap, questions, answers, jobs, catalog, client)
    assert report_again["summary_fa"] == report["summary_fa"]
    assert client.calls == 1


def test_generate_user_feedback_fallback_when_client_fails():
    _reset_cache()
    gap, questions, answers, jobs, catalog = _sample_inputs()
    report = generate_user_feedback(gap, questions, answers, jobs, catalog, FailingAvalAIClient())
    assert report["summary_fa"]
    assert report["course_plan_fa"]
