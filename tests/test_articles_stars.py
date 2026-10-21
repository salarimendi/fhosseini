# -*- coding: utf-8 -*-
"""تست‌های هدفمند: نرمال‌سازی آدرس تصاویر مقالات و تبدیل ساعت ایران به UTC."""
import base64
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_utils():
    pytest.importorskip("bleach")
    pytest.importorskip("slugify")
    from app.articles import utils
    return utils


def test_relative_and_absolute_media_urls_are_normalized():
    utils = _load_utils()
    html = ('<img src="../../articles/media/a.png"><img src="media/b.jpg">'
            '<img src="https://x.ir/articles/media/c.gif"><img src="https://o.com/e.png">')
    out = utils.normalize_media_urls(html)
    assert 'src="/articles/media/a.png"' in out
    assert 'src="/articles/media/b.jpg"' in out
    assert 'src="/articles/media/c.gif"' in out
    assert 'https://o.com/e.png' in out


def test_data_uri_image_is_saved_as_file(tmp_path):
    utils = _load_utils()
    png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 16).decode()
    out = utils.sanitize_html(f'<p><img src="data:image/png;base64,{png}"></p>', str(tmp_path))
    names = utils.extract_media_filenames(out)
    assert len(names) == 1 and (tmp_path / next(iter(names))).exists()


def _load_stars():
    sw = types.ModuleType("swisseph")
    for n in "SUN MOON MERCURY VENUS MARS JUPITER SATURN".split():
        setattr(sw, n, 1)
    sw.set_ephe_path = lambda p: None
    sys.modules.setdefault("swisseph", sw)
    pytest.importorskip("flask")
    from app.routes import stars
    return stars


@pytest.mark.parametrize("value,tz,expected", [
    ("2026-03-21T02:00", "iran", "2026-03-20 22:30"),   # عبور از مرز روز
    ("2026-01-01T00:10", "iran", "2025-12-31 20:40"),   # عبور از مرز سال
    ("2026-03-21T03:30", "iran", "2026-03-21 00:00"),
    ("2026-03-01T12:00", "utc", "2026-03-01 12:00"),
    ("2026-03-01T12:00", "bogus", "2026-03-01 12:00"),  # منطقه‌ی نامعتبر -> UTC
])
def test_iran_time_to_utc(value, tz, expected):
    stars = _load_stars()
    utc, _, _ = stars.parse_local_to_utc(value, tz)
    assert utc.strftime("%Y-%m-%d %H:%M") == expected
