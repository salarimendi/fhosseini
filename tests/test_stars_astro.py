"""
تست سبک صفحه‌ی اجرام سماوی با یک «تقویم ساختگی» (بدون نیاز به Swiss Ephemeris).
دقت مدل ساختگی پایین است؛ هدف فقط بررسی منطق و رندر قالب است.
"""
import math
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _fake_swisseph():
    sw = types.ModuleType("swisseph")
    for i, n in enumerate("SUN MOON MERCURY VENUS MARS JUPITER SATURN".split()):
        setattr(sw, n, i)
    sw.FLG_SWIEPH, sw.FLG_SPEED, sw.FLG_EQUATORIAL = 2, 256, 2048
    sw.set_ephe_path = lambda p: None
    # (طول در J2000، حرکت روزانه)
    model = {0: (280.46, 0.98565), 1: (218.32, 13.17640), 2: (252.0, 1.2),
             3: (181.0, 1.2), 4: (355.0, 0.52), 5: (34.0, 0.083), 6: (50.0, 0.033)}
    eps = math.radians(23.439)

    def calc_ut(jd, body, flags=258):
        d = jd - 2451545.0
        l0, n = model[body]
        lon = (l0 + n * d) % 360
        lat = 5.1 * math.sin(math.radians(lon - 90)) if body == 1 else 0.0
        speed = n
        dist = 384400 / 149597870.7 if body == 1 else 1.0
        if flags & 2048:
            lr, br = math.radians(lon), math.radians(lat)
            ra = math.degrees(math.atan2(math.sin(lr) * math.cos(eps) - math.tan(br) * math.sin(eps), math.cos(lr))) % 360
            dec = math.degrees(math.asin(math.sin(br) * math.cos(eps) + math.cos(br) * math.sin(eps) * math.sin(lr)))
            return (ra, dec, dist, 0, 0, 0), flags
        return (lon, lat, dist, speed, 0, 0), flags

    sw.calc_ut = calc_ut
    sw.sidtime = lambda jd: (18.697374558 + 24.06570982441908 * (jd - 2451545.0)) % 24
    return sw


@pytest.fixture()
def astro(monkeypatch):
    monkeypatch.setitem(sys.modules, "swisseph", _fake_swisseph())
    monkeypatch.syspath_prepend(str(ROOT))
    for m in [k for k in sys.modules if k.startswith("app.utils.astro")]:
        monkeypatch.delitem(sys.modules, m)
    pytest.importorskip("flask")
    import importlib
    return importlib.import_module("app.utils.astro")


def test_sign_abbreviations_and_rounding(astro):
    assert [s[2] for s in astro.SIGNS] == ["ها", "ا", "ب", "ج", "د", "ه", "و", "ز", "ح", "ط", "ی", "یا"]
    # رُند ثانیه نباید درجه‌ی ۳۰ بسازد: ۲۹°۵۹′۵۹٫۹″ حمل -> ۰° ثور
    si, d, m, s = astro.lon_to_sign(29.99999)
    assert (si, d, m, s) == (1, 0, 0, 0)


def test_station_states(astro):
    mars = astro.BODY_BY_KEY["mars"]
    assert astro.motion_state(mars, 0.3, 1)["key"] == "mustaqim"
    assert astro.motion_state(mars, 0.01, 1)["key"] == "muqim"
    assert astro.motion_state(mars, -0.3, 1)["key"] == "raji"
    assert astro.motion_state(astro.BODY_BY_KEY["sun"], 1, 1) is None


def test_aspect_rules(astro):
    def row(key, lon, speed):
        return dict(key=key, name=key, glyph="x", color="#000", longitude=lon, speed=speed)
    jorms = {"sun": 35, "moon": 12, "saturn": 9, "mars": 8}
    # تسدیس ایمن: قمر (سریع) ۶۰ درجه پیش از شمس (کندتر)
    rows = [row("sun", 100.0, 1.0), row("moon", 40.0, 13.0)]
    sext = [a for a in astro.calculate_aspects(rows, jorms) if a["type"] == "sext"][0]
    assert sext["fast"]["key"] == "moon" and "تسدیس ایمن" in sext["tags"] and sext["state"] == "exact"
    # ایسر: قمر پس از شمس
    rows = [row("sun", 100.0, 1.0), row("moon", 160.0, 13.0)]
    assert "تسدیس ایسر" in [a for a in astro.calculate_aspects(rows, jorms) if a["type"] == "sext"][0]["tags"]
    # اجتماع و استقبال
    rows = [row("sun", 100.0, 1.0), row("moon", 99.0, 13.0)]
    assert "اجتماع" in [a for a in astro.calculate_aspects(rows, jorms) if a["type"] == "conj"][0]["tags"]
    rows = [row("sun", 100.0, 1.0), row("moon", 280.5, 13.0)]
    assert "استقبال" in [a for a in astro.calculate_aspects(rows, jorms) if a["type"] == "opp"][0]["tags"]
    # ابطال: جداشونده با فاصله‌ی بیشتر از نصف مجموع جرم (۲۰/۲ = ۱۰) حذف می‌شود
    rows = [row("mars", 100.0, 0.5), row("saturn", 90.0 - 0.0, 0.1)]
    jm = {"mars": 8, "saturn": 12}
    assert [a for a in astro.calculate_aspects(rows, jm) if a["type"] == "conj"] == []


def test_evening_report_and_page(astro, monkeypatch):
    dt = datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc)
    a = astro.build_analysis(dt, "qom", {b["key"]: b["jorm"] for b in astro.BODIES}, 1.0)
    ev = a["evening"]
    assert ev and 13.0 < ev["sunset"].hour + ev["sunset"].minute / 60 < 15.0  # غروب قم ~ ۱۷ به وقت ایران
    assert -180 <= ev["elong"] <= 180 and a["evenings"]
    assert all(len(r["sign_abbr"]) >= 1 for r in a["rows"])

    # رندر قالب با پایه‌ی ساده
    from flask import Flask, render_template
    from jinja2 import DictLoader, ChoiceLoader, FileSystemLoader
    app = Flask(__name__)
    app.jinja_loader = ChoiceLoader([
        DictLoader({"base.html": "{% block head %}{% endblock %}{% block content %}{% endblock %}"}),
        FileSystemLoader(str(ROOT / "app" / "templates")),
    ])
    app.jinja_env.globals["csrf_token"] = lambda: "t"
    for m in [k for k in sys.modules if k == "app.routes.stars"]:
        monkeypatch.delitem(sys.modules, m)
    import importlib
    stars = importlib.import_module("app.routes.stars")
    with app.test_request_context():
        html = render_template(
            "stars/calculate.html", a=a, utc=dt, local_dt=dt, iran_dt=dt.astimezone(astro.IRAN_TZ),
            date_value="2026-11-10T17:30", tz_key="iran", city_key="qom", cities=astro.CITIES,
            bodies=astro.BODIES, jorms={b["key"]: b["jorm"] for b in astro.BODIES}, factor=1.0,
            aspect_types=astro.ASPECTS, crit=astro.DEFAULT_CRITERIA, tier_labels=astro.TIER_LABELS,
            jdate=astro.jalali_str, jdt=astro.fmt_local, dms_s=astro.dms_signed, min_sec=astro.min_sec, hms=astro.hms,
            timezones={k: v[0] for k, v in stars.TIMEZONES.items()},
        )
    assert "بعد سواء" in html and "بعد معدل" in html and "عرض (°)" in html
    assert 'data-bodies="' in html and "built-in" not in html  # باگ فیلتر: کلید keys
    assert "(استقامت)" not in html
    out = stars.localize_digits(html)
    assert "۱۴۰۵/۰۸/۱۹" in out or "۱۴۰۵/۰۸/۲۰" in out  # تاریخ شمسی با ارقام فارسی


def test_tusi_criteria(astro):
    c = astro.classify_evening
    assert c(-3, 5)[0] == "before" and c(12, -1)[0] == "no"
    assert c(12, 9)[0] == "unlikely"
    assert [c(12, x)[1] for x in (11, 13, 15, 17, 19)] == astro.TIER_LABELS
    assert c(8, 12.5)[0] == "possible" and c(8, 11)[0] == "unlikely"


def test_dms_and_trine_side(astro):
    assert astro.dms_signed(5.74) == "+5° 44′ 24″" and astro.min_sec(23.5) == "+23 دقیقه و 30 ثانیه"
    row = lambda k, lon, sp: dict(key=k, name=k, glyph="x", color="#000", longitude=lon, speed=sp)
    r = [row("sun", 100.0, 1.0), row("moon", 220.0, 13.0)]  # قمر ۱۲۰ درجه پس از شمس
    tri = [a for a in astro.calculate_aspects(r, {"sun": 35, "moon": 12}) if a["type"] == "trine"][0]
    assert "تثلیث ایسر" in tri["tags"]


def test_hms_and_no_duplicate(astro):
    assert astro.hms(22.4) == "+00:22:24" and astro.hms(-1.5) == "-00:01:30" and astro.hms(1836, False) == "30:36:00"
    assert not astro.classify_evening(-3, 5)[2].startswith("قبل از مقارنه")


def test_jalali(astro):
    from datetime import date
    assert astro.jalali_str(date(2026, 3, 21)) == "1405/01/01"


@pytest.mark.parametrize("value,tz,expected", [
    ("2026-03-21T02:00", "iran", "2026-03-20 22:30"),
    ("2026-01-01T00:10", "iran", "2025-12-31 20:40"),
    ("2026-03-01T12:00", "utc", "2026-03-01 12:00"),
    ("2026-03-01T12:00", "bogus", "2026-03-01 08:30"),  # منطقه‌ی نامعتبر -> ایران (پیش‌فرض)
])
def test_iran_time_to_utc(astro, monkeypatch, value, tz, expected):
    for m in [k for k in sys.modules if k == "app.routes.stars"]:
        monkeypatch.delitem(sys.modules, m)
    import importlib
    stars = importlib.import_module("app.routes.stars")
    utc, _, _ = stars.parse_local_to_utc(value, tz)
    assert utc.strftime("%Y-%m-%d %H:%M") == expected
