from datetime import datetime, timedelta, timezone
from pathlib import Path

import swisseph as swe
from flask import Blueprint, render_template, request


stars_bp = Blueprint("stars", __name__)

EPHE_PATH = Path(__file__).resolve().parent.parent / "ephe"
swe.set_ephe_path(str(EPHE_PATH))

BODIES = {
    "خورشید ☉": swe.SUN,
    "ماه ☽": swe.MOON,
    "عطارد ☿": swe.MERCURY,
    "زهره ♀": swe.VENUS,
    "مریخ ♂": swe.MARS,
    "مشتری ♃": swe.JUPITER,
    "زحل ♄": swe.SATURN,
}

SIGNS = [
    ("حمل", "♈️"),
    ("ثور", "♉️"),
    ("جوزا", "♊️"),
    ("سرطان", "♋️"),
    ("اسد", "♌️"),
    ("سنبله", "♍️"),
    ("میزان", "♎️"),
    ("عقرب", "♏️"),
    ("قوس", "♐️"),
    ("جدی", "♑️"),
    ("دلو", "♒️"),
    ("حوت", "♓️"),
]


# منطقه‌های زمانی قابل انتخاب برای ورودی. محاسبات همیشه با UTC انجام می‌شود.
# ایران از ۱۴۰۱ ساعت تابستانی ندارد، بنابراین UTC+03:30 ثابت است.
TIMEZONES = {
    "utc": ("UTC", timezone.utc),
    "iran": ("ایران (UTC+03:30)", timezone(timedelta(hours=3, minutes=30))),
}
DEFAULT_TZ = "utc"
INPUT_FORMAT = "%Y-%m-%dT%H:%M"


def parse_local_to_utc(date_value, tz_key):
    """
    مقدار datetime-local را در منطقه‌ی زمانی انتخاب‌شده می‌خواند و
    معادل UTC آن را برمی‌گرداند (مرز روز/ماه/سال به‌درستی جابه‌جا می‌شود).
    """
    if tz_key not in TIMEZONES:
        tz_key = DEFAULT_TZ
    naive = datetime.fromisoformat(date_value).replace(second=0, microsecond=0)
    local_dt = naive.replace(tzinfo=TIMEZONES[tz_key][1])
    return local_dt.astimezone(timezone.utc), local_dt, tz_key


def longitude_to_dms(longitude, sign_symbol):
    longitude = longitude % 360
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30

    degree = int(degree_in_sign)
    minutes_float = (degree_in_sign - degree) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)

    if seconds == 60:
        seconds = 0
        minutes += 1

    if minutes == 60:
        minutes = 0
        degree += 1

    if degree == 30:
        degree = 0

    dms = f"{degree}°{sign_symbol}{minutes:02d}'{seconds:02d}\""
    return sign_index, dms


def calculate_planets(dt):
    utc_hour = dt.hour + dt.minute / 60 + dt.second / 3600
    julian_day = swe.julday(dt.year, dt.month, dt.day, utc_hour)
    planets = []

    for name, body in BODIES.items():
        positions, _, _ = swe.calc_ut(julian_day, body)
        longitude = positions[0]
        speed = positions[3]

        sign_index, dms = longitude_to_dms(
            longitude,
            SIGNS[int(longitude % 360 // 30)][1],
        )
        sign_name, sign_symbol = SIGNS[sign_index]

        description = ""

        if body == swe.MOON and 210 < longitude <= 240:
            description = "قمر در برج عقرب"

        planets.append({
            "name": name,
            "sign": f"{sign_name} {sign_symbol}",
            "dms": f"{dms}{'r' if speed < 0 else ''}",
            "longitude": longitude,
            "speed": speed,
            "description": description,
        })

    return planets, julian_day


@stars_bp.route("/calculate", methods=["GET", "POST"])
def calculate():
    now_utc = datetime.now(timezone.utc)
    tz_key = DEFAULT_TZ
    date_value = now_utc.strftime(INPUT_FORMAT)

    if request.method == "POST":
        tz_key = request.form.get("tz", DEFAULT_TZ)
        if tz_key not in TIMEZONES:
            tz_key = DEFAULT_TZ
        date_value = request.form.get("date_time") or now_utc.astimezone(
            TIMEZONES[tz_key][1]
        ).strftime(INPUT_FORMAT)

    try:
        dt, local_dt, tz_key = parse_local_to_utc(date_value, tz_key)
    except ValueError:
        tz_key = DEFAULT_TZ
        date_value = now_utc.strftime(INPUT_FORMAT)
        dt, local_dt, tz_key = parse_local_to_utc(date_value, tz_key)

    planets, julian_day = calculate_planets(dt)

    return render_template(
        "stars/calculate.html",
        planets=planets,
        utc=dt,
        local_dt=local_dt,
        julian_day=julian_day,
        date_value=date_value,
        tz_key=tz_key,
        timezones={k: v[0] for k, v in TIMEZONES.items()},
    )
