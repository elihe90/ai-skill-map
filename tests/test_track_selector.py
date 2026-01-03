from core.track_selector import select_track


def test_track_selector_content():
    result = select_track("درآمد سریع", "۳–۵ ساعت", "تولید محتوا و شبکه‌های اجتماعی")
    assert result["track"] == "content"


def test_track_selector_automation():
    result = select_track("ارتقای شغلی", "۶–۱۰ ساعت", "اتوماسیون و بهبود کارهای اداری/گزارش")
    assert result["track"] == "automation"


def test_track_selector_technical():
    result = select_track("تغییر مسیر فنی", "بیشتر از ۱۰ ساعت", "کار فنی و کدنویسی/حل مسئله")
    assert result["track"] == "technical"
