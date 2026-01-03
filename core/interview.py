from typing import Iterable, TypedDict


class InterviewScores(TypedDict):
    problem_solving_score: int
    execution_score: int
    ai_mindset_score: int
    learning_score: int
    planning_score: int


PROBLEM_SOLVING_KEYWORDS = (
    "حل",
    "تحلیل",
    "مسئله",
    "ریشه",
    "راهکار",
    "گزینه",
)
EXECUTION_KEYWORDS = (
    "اجرا",
    "برنامه",
    "گام",
    "زمان",
    "پیاده",
    "نقشه",
    "تحویل",
)
AI_MINDSET_KEYWORDS = (
    "داده",
    "مدل",
    "آزمایش",
    "یادگیری",
    "بازخورد",
    "هوش",
    "ai",
    "الگوریتم",
)
LEARNING_KEYWORDS = (
    "یادگیری",
    "تمرین",
    "آموزش",
    "منبع",
    "پیشرفت",
    "مطالعه",
)
PLANNING_KEYWORDS = (
    "برنامه",
    "زمان",
    "اولویت",
    "تقویم",
    "زمان بندی",
    "برآورد",
)


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _score_dimension(text: str, keywords: tuple[str, ...], length_points: int) -> int:
    keyword_points = min(3, _keyword_hits(text, keywords))
    return min(5, length_points + keyword_points)


def score_interview(answers: Iterable[str]) -> InterviewScores:
    joined = " ".join(answer.strip() for answer in answers if answer).lower()
    total_words = len(joined.split())
    length_points = min(2, total_words // 60)

    return InterviewScores(
        problem_solving_score=_score_dimension(
            joined, PROBLEM_SOLVING_KEYWORDS, length_points
        ),
        execution_score=_score_dimension(joined, EXECUTION_KEYWORDS, length_points),
        ai_mindset_score=_score_dimension(joined, AI_MINDSET_KEYWORDS, length_points),
        learning_score=_score_dimension(joined, LEARNING_KEYWORDS, length_points),
        planning_score=_score_dimension(joined, PLANNING_KEYWORDS, length_points),
    )
