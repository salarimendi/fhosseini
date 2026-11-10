import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request

from app.utils import astro

stars_bp = Blueprint("stars", __name__)

# منطقه‌های زمانی قابل انتخاب برای ورودی. محاسبات همیشه با UTC انجام می‌شود.
# ایران از ۱۴۰۱ ساعت تابستانی ندارد، بنابراین UTC+03:30 ثابت است.
TIMEZONES = {
    "iran": ("ایران (UTC+03:30)", timezone(timedelta(hours=3, minutes=30))),
    "utc": ("UTC", timezone.utc),
}
DEFAULT_TZ = "iran"
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


def _read_jorms(form):
    """جرم هر کوکب (درجه)؛ مقدار نامعتبر به پیش‌فرض برمی‌گردد."""
    jorms = {}
    for body in astro.BODIES:
        raw = form.get(f"jorm_{body['key']}", "")
        try:
            value = float(raw)
            if not 0 <= value <= 60:
                raise ValueError
        except ValueError:
            value = float(body["jorm"])
        jorms[body["key"]] = value
    return jorms


def _read_factor(form):
    try:
        value = float(form.get("stat_factor", ""))
        if not 0.1 <= value <= 5:
            raise ValueError
    except ValueError:
        value = astro.STATION_DEFAULT_FACTOR
    return value


def _read_criteria(form):
    """معیار طوسی قابل ویرایش؛ مقدار نامعتبر یا غیرصعودی به پیش‌فرض برمی‌گردد."""
    d = astro.DEFAULT_CRITERIA
    try:
        sawa = float(form.get("crit_sawa", ""))
        low = float(form.get("crit_low", ""))
        tiers = [float(form.get(f"crit_t{i}", "")) for i in range(1, 6)]
        ok = (0 < sawa <= 60 and 0 < low <= 60
              and all(0 < x <= 90 for x in tiers) and tiers == sorted(tiers))
    except ValueError:
        ok = False
    if not ok:
        return dict(sawa_min=d["sawa_min"], tiers=list(d["tiers"]), low_maadal=d["low_maadal"])
    return dict(sawa_min=sawa, tiers=tiers, low_maadal=low)


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_SKIP = re.compile(r"(<style.*?</style>|<script.*?</script>|<[^>]+>)", re.S | re.I)


def localize_digits(html):
    """ارقام متن محتوای صفحه (داخل main) را فارسی می‌کند؛ تگ‌ها، مقدار فیلدها، CSS و JS و بقیه‌ی قالب دست‌نخورده می‌مانند."""
    start = html.find('<main class="st-page"')
    end = html.find("</main>", start)
    if start < 0 or end < 0:
        return html
    return html[:start] + _localize(html[start:end]) + html[end:]


def _localize(html):
    parts = _SKIP.split(html)
    for i in range(0, len(parts), 2):  # فقط بخش‌های متنی
        text = re.sub(r"(?<=\d)\.(?=\d)", "٫", parts[i])
        parts[i] = text.translate(_FA_DIGITS)
    return "".join(parts)


@stars_bp.route("/calculate", methods=["GET", "POST"])
def calculate():
    now_utc = datetime.now(timezone.utc)
    tz_key = DEFAULT_TZ
    city_key = astro.DEFAULT_CITY
    jorms = {b["key"]: float(b["jorm"]) for b in astro.BODIES}
    factor = astro.STATION_DEFAULT_FACTOR
    crit = _read_criteria({})
    date_value = now_utc.astimezone(TIMEZONES[tz_key][1]).strftime(INPUT_FORMAT)

    if request.method == "POST":
        tz_key = request.form.get("tz", DEFAULT_TZ)
        if tz_key not in TIMEZONES:
            tz_key = DEFAULT_TZ
        city_key = request.form.get("city", astro.DEFAULT_CITY)
        if city_key not in astro.CITIES:
            city_key = astro.DEFAULT_CITY
        jorms = _read_jorms(request.form)
        factor = _read_factor(request.form)
        crit = _read_criteria(request.form)
        date_value = request.form.get("date_time") or now_utc.astimezone(
            TIMEZONES[tz_key][1]
        ).strftime(INPUT_FORMAT)

    try:
        dt, local_dt, tz_key = parse_local_to_utc(date_value, tz_key)
    except ValueError:
        tz_key = DEFAULT_TZ
        date_value = now_utc.astimezone(TIMEZONES[tz_key][1]).strftime(INPUT_FORMAT)
        dt, local_dt, tz_key = parse_local_to_utc(date_value, tz_key)

    analysis = astro.build_analysis(dt, city_key, jorms, factor, crit)

    html = render_template(
        "stars/calculate.html",
        a=analysis,
        utc=dt,
        local_dt=local_dt,
        iran_dt=dt.astimezone(astro.IRAN_TZ),
        date_value=date_value,
        tz_key=tz_key,
        city_key=city_key,
        cities=astro.CITIES,
        bodies=astro.BODIES,
        jorms=jorms,
        factor=factor,
        aspect_types=astro.ASPECTS,
        crit=crit,
        tier_labels=astro.TIER_LABELS,
        jdate=astro.jalali_str,
        jdt=astro.fmt_local,
        timezones={k: v[0] for k, v in TIMEZONES.items()},
    )
    return localize_digits(html)
