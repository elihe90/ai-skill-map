from core.job_filter import filter_job_mapping_by_track


def test_content_track_filters_ml_jobs():
    job_mapping = {
        "reachable_jobs": [
            {"title_fa": "شغل محتوا", "domain": "content"},
            {"title_fa": "شغل ML", "domain": "machine_learning"},
        ],
        "next_level_jobs": [
            {"title_fa": "شغل مارکتینگ", "domain": "marketing"},
            {"title_fa": "شغل داده", "domain": "data"},
        ],
    }
    filtered = filter_job_mapping_by_track(job_mapping, "content")
    titles = {item["title_fa"] for item in filtered["reachable_jobs"]}
    assert "شغل محتوا" in titles
    assert "شغل ML" not in titles
    next_titles = {item["title_fa"] for item in filtered["next_level_jobs"]}
    assert "شغل مارکتینگ" in next_titles
    assert "شغل داده" not in next_titles


def test_technical_track_filters_content_jobs():
    job_mapping = {
        "reachable_jobs": [
            {"title_fa": "شغل محتوا", "domain": "content"},
            {"title_fa": "شغل AI", "domain": "ai"},
        ],
        "next_level_jobs": [
            {"title_fa": "شغل داده", "domain": "data"},
            {"title_fa": "شغل مارکتینگ", "domain": "marketing"},
        ],
    }
    filtered = filter_job_mapping_by_track(job_mapping, "technical")
    titles = {item["title_fa"] for item in filtered["reachable_jobs"]}
    assert "شغل AI" in titles
    assert "شغل محتوا" not in titles
    next_titles = {item["title_fa"] for item in filtered["next_level_jobs"]}
    assert "شغل داده" in next_titles
    assert "شغل مارکتینگ" not in next_titles
