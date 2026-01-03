from __future__ import annotations

from typing import Any, Dict, List, Optional


class SkillGapEngine:
    """Simple, explainable gap evaluation using keywords, evidence, and scores."""

    _KEYWORDS: Dict[str, List[str]] = {
        "GAP_CONTENT_PUBLISHABLE_OUTPUT": [
            "خروجی قابل انتشار",
            "قابل انتشار",
            "ویرایش",
            "پولیش",
        ],
        "GAP_PROMPTING_FOR_CONTENT": [
            "پرامپت",
            "دستور",
            "قالب پرامپت",
            "رول",
        ],
        "GAP_CONTENT_PLANNING": [
            "تقویم محتوا",
            "برنامه محتوا",
            "برنامه ریزی",
            "CTA",
        ],
        "GAP_MULTIMODAL_CONTENT": [
            "چندرسانه",
            "تصویر",
            "ویدئو",
            "انیمیشن",
        ],
        "GAP_AUDIENCE_FIT_WITH_AI": [
            "پرسونا",
            "مخاطب",
            "لحن",
            "بازخورد",
        ],
        "GAP_PORTFOLIO_WITH_AI": [
            "نمونه کار",
            "نمونه‌کار",
            "پروژه واقعی",
            "پورتفولیو",
        ],
    }

    _SCORE_MAP: Dict[str, str] = {
        "GAP_CONTENT_PUBLISHABLE_OUTPUT": "execution",
        "GAP_PROMPTING_FOR_CONTENT": "ai_mindset",
        "GAP_CONTENT_PLANNING": "planning",
        "GAP_MULTIMODAL_CONTENT": "learning",
        "GAP_AUDIENCE_FIT_WITH_AI": "problem_solving",
        "GAP_PORTFOLIO_WITH_AI": "execution",
    }

    def __init__(self, gaps_json: dict):
        self.gaps = gaps_json.get("gaps", []) if isinstance(gaps_json, dict) else []

    def evaluate_gaps(
        self,
        interview_answers: str,
        interview_scores: dict,
        evidence: Optional[dict] = None,
    ) -> dict:
        """
        Returns gap status per gap_id.
        Status values: "solved" or "unsolved".
        """
        answers_text = str(interview_answers or "")
        answers_text = answers_text.replace("‌", " ")
        scores = interview_scores if isinstance(interview_scores, dict) else {}
        evidence_payload = evidence if isinstance(evidence, dict) else {}

        output: Dict[str, Any] = {}
        for gap in self.gaps:
            gap_id = gap.get("gap_id")
            if not gap_id:
                continue
            solved = False

            if self._has_evidence(gap_id, evidence_payload):
                solved = True

            if not solved and self._keyword_hit(gap_id, answers_text):
                solved = True

            if not solved:
                score_key = self._SCORE_MAP.get(gap_id)
                if score_key and int(scores.get(score_key, 0)) >= 4:
                    solved = True

            next_action = None if solved else self.get_next_action(gap_id)
            output[gap_id] = {
                "status": "solved" if solved else "unsolved",
                "next_action": next_action,
            }

        return output

    def get_next_action(self, gap_id: str) -> Optional[dict]:
        """Return the first block title and its first micro-step for a gap."""
        for gap in self.gaps:
            if gap.get("gap_id") != gap_id:
                continue
            blocks = gap.get("blocks", []) if isinstance(gap.get("blocks"), list) else []
            if not blocks:
                return None
            first_block = blocks[0] if isinstance(blocks[0], dict) else None
            if not first_block:
                return None
            micro_steps = first_block.get("micro_steps_fa", [])
            first_step = micro_steps[0] if isinstance(micro_steps, list) and micro_steps else ""
            return {
                "title_fa": first_block.get("title_fa", ""),
                "micro_step_fa": first_step,
            }
        return None

    def _keyword_hit(self, gap_id: str, answers_text: str) -> bool:
        keywords = self._KEYWORDS.get(gap_id, [])
        for keyword in keywords:
            if keyword and keyword in answers_text:
                return True
        return False

    def _has_evidence(self, gap_id: str, evidence: dict) -> bool:
        if evidence.get(gap_id):
            return True
        solved_gaps = evidence.get("solved_gaps")
        if isinstance(solved_gaps, list) and gap_id in solved_gaps:
            return True
        return False
