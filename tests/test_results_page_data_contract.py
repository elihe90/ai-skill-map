from ui.results_page import normalize_session_payload


def test_normalize_session_payload_handles_missing():
    payload = normalize_session_payload(None, None, None)
    assert isinstance(payload["gap"], dict)
    assert isinstance(payload["feedback"], dict)
    assert isinstance(payload["job_mapping"], dict)


def test_normalize_session_payload_passes_dicts():
    gap = {"training_level": "A"}
    feedback = {"summary_fa": "ok"}
    job_mapping = {"reachable_jobs": []}
    payload = normalize_session_payload(gap, feedback, job_mapping)
    assert payload["gap"] == gap
    assert payload["feedback"] == feedback
    assert payload["job_mapping"] == job_mapping
