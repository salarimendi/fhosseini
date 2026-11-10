"""
محاسبات نجومی صفحه‌ی «اجرام سماوی و قمر در عقرب».

- طول و عرض هر کوکب از منطقةالبروج (Swiss Ephemeris)
- حالت حرکت خمسه‌ی متحیره: استقامت / اقامت / رجعت
- اتصالات (مقارنه، تسدیس، تربیع، تثلیث، مقابله) با حدود جرم
- اجتماع و استقبال، احتراق، ایمن/ایسر در تسدیس و تربیع و تثلیث و مقابله
- بعد السواء و بعد المعدل برای استهلال در افق شهرهای انتخابی

همه‌ی زمان‌ها در محاسبه UTC هستند و فقط هنگام نمایش به وقت ایران برمی‌گردند.
"""
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import swisseph as swe

EPHE_PATH = Path(__file__).resolve().parent.parent / "ephe"
swe.set_ephe_path(str(EPHE_PATH))

# پرچم‌های Swiss Ephemeris (مقدار عددی پیش‌فرض برای محیط‌های بدون ثابت)
_SWIEPH = getattr(swe, "FLG_SWIEPH", 2)
_SPEED = getattr(swe, "FLG_SPEED", 256)
_EQUATORIAL = getattr(swe, "FLG_EQUATORIAL", 2048)
FLAGS_ECL = _SWIEPH | _SPEED
FLAGS_EQ = _SWIEPH | _SPEED | _EQUATORIAL

UTC = timezone.utc
IRAN_TZ = timezone(timedelta(hours=3, minutes=30))
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_UNIX_JD = 2440587.5
AU_KM = 149597870.7

# ---------------------------------------------------------------- داده‌ها

# (نام، نماد، حرف اختصاری در هیئت، عنصر)
SIGNS = [
    ("حمل", "♈︎", "ها", "fire"),
    ("ثور", "♉︎", "ا", "earth"),
    ("جوزا", "♊︎", "ب", "air"),
    ("سرطان", "♋︎", "ج", "water"),
    ("اسد", "♌︎", "د", "fire"),
    ("سنبله", "♍︎", "ه", "earth"),
    ("میزان", "♎︎", "و", "air"),
    ("عقرب", "♏︎", "ز", "water"),
    ("قوس", "♐︎", "ح", "fire"),
    ("جدی", "♑︎", "ط", "earth"),
    ("دلو", "♒︎", "ی", "air"),
    ("حوت", "♓︎", "یا", "water"),
]
SCORPIO_INDEX = 7

# جرم (درجه) طبق مقادیر درخواستی؛ tol = تلورانس اقامت (درجه در روز)
BODIES = [
    dict(key="sun", name="شمس", glyph="☉", ephe=swe.SUN, jorm=35, wanderer=False, tol=None, color="#f59e0b"),
    dict(key="moon", name="قمر", glyph="☽", ephe=swe.MOON, jorm=12, wanderer=False, tol=None, color="#94a3b8"),
    dict(key="mercury", name="عطارد", glyph="☿", ephe=swe.MERCURY, jorm=7, wanderer=True, tol=0.10, color="#0ea5e9"),
    dict(key="venus", name="زهره", glyph="♀", ephe=swe.VENUS, jorm=7, wanderer=True, tol=0.08, color="#ec4899"),
    dict(key="mars", name="مریخ", glyph="♂", ephe=swe.MARS, jorm=8, wanderer=True, tol=0.04, color="#ef4444"),
    dict(key="jupiter", name="مشتری", glyph="♃", ephe=swe.JUPITER, jorm=9, wanderer=True, tol=0.02, color="#f97316"),
    dict(key="saturn", name="زحل", glyph="♄", ephe=swe.SATURN, jorm=9, wanderer=True, tol=0.015, color="#64748b"),
]
BODY_BY_KEY = {b["key"]: b for b in BODIES}

ASPECTS = [
    dict(key="conj", name="مقارنه", glyph="☌", angle=0),
    dict(key="sext", name="تسدیس", glyph="⚹", angle=60),
    dict(key="quad", name="تربیع", glyph="□", angle=90),
    dict(key="trine", name="تثلیث", glyph="△", angle=120),
    dict(key="opp", name="مقابله", glyph="☍", angle=180),
]

CITIES = {
    "qom": dict(name="قم", lat=34.6399, lon=50.8759),
    "tehran": dict(name="تهران", lat=35.6892, lon=51.3890),
    "sari": dict(name="ساری", lat=36.5633, lon=53.0601),
    "gonabad": dict(name="گناباد", lat=34.3529, lon=58.6844),
}
DEFAULT_CITY = "qom"

# معیار رؤیت هلال بر اساس زیج ایلخانی (پژوهش حمیدرضا گیاهی‌یزدی).
# sawa_min: حد بعد سواء؛ tiers: مرزهای بعد معدل (درجه) برای بعد سواء >= حد؛
# low_maadal: حداقل بعد معدل وقتی بعد سواء کمتر از حد است.
DEFAULT_CRITERIA = dict(sawa_min=10.0, tiers=[10.0, 12.0, 14.0, 16.0, 18.0], low_maadal=12.0)
TIER_LABELS = ["هلال باریک", "هلال متوسط", "هلال روشن", "رؤیت‌پذیر", "رؤیت بسیار آسان"]
SAWA_THRESHOLD = DEFAULT_CRITERIA["sawa_min"]
STATION_DEFAULT_FACTOR = 1.0


# ---------------------------------------------------------------- زمان

def to_jd(dt):
    return (dt - _EPOCH).total_seconds() / 86400.0 + _UNIX_JD


def from_jd(jd):
    return _EPOCH + timedelta(days=jd - _UNIX_JD)


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def jalali_str(d):
    """تاریخ شمسی به‌صورت 1405/08/19 (ارقام در لایه‌ی نمایش فارسی می‌شوند)."""
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy}/{jm:02d}/{jd:02d}"


def fmt_local(dt):
    """تاریخ شمسی و ساعت به وقت ایران."""
    loc = dt.astimezone(IRAN_TZ)
    return f"{jalali_str(loc)} {loc:%H:%M}"


def fmt_hm(dt):
    return dt.astimezone(IRAN_TZ).strftime("%H:%M:%S")


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def dms_signed(deg):
    """درجه‌ی علامت‌دار به درجه/دقیقه/ثانیه‌ی فلکی (تا ثانیه)."""
    d, m, sec = dms_parts(deg)
    return f"{'-' if deg < 0 and (d or m or sec) else '+'}{d}° {m:02d}′ {sec:02d}″"


def min_sec(minutes):
    """دقیقه‌ی علامت‌دار (اعشاری) به دقیقه و ثانیه‌ی زمانی."""
    total = int(round(abs(minutes) * 60))
    m, sec = divmod(total, 60)
    sign = "-" if minutes < 0 and total else "+"
    return f"{sign}{m} دقیقه و {sec:02d} ثانیه"


def hms(minutes, signed=True):
    """دقیقه (اعشاری) به ساعت زمانی HH:MM:SS؛ با علامت اختیاری."""
    total = int(round(abs(minutes) * 60))
    h, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    sign = ("-" if minutes < 0 and total else "+") if signed else ""
    return f"{sign}{h:02d}:{m:02d}:{sec:02d}"


def fmt_duration(hours):
    """مدت (ساعت، علامت‌دار) به متن فارسی."""
    h = abs(hours)
    if h >= 48:
        days = int(h // 24)
        rest = int(round(h - days * 24))
        return f"{days} روز و {rest} ساعت" if rest else f"{days} روز"
    total_min = int(round(h * 60))
    hh, mm = divmod(total_min, 60)
    if hh and mm:
        return f"{hh} ساعت و {mm} دقیقه"
    if hh:
        return f"{hh} ساعت"
    return f"{mm} دقیقه"


# ---------------------------------------------------------------- مختصات

def dms_parts(value):
    sec = int(round(abs(value) * 3600))
    d, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return d, m, s


def lon_to_sign(longitude):
    """(اندیس برج، درجه، دقیقه، ثانیه) با رُند صحیح که مرز برج را نمی‌شکند."""
    total = int(round((longitude % 360.0) * 3600)) % (360 * 3600)
    sign_index, rem = divmod(total, 30 * 3600)
    d, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return sign_index, d, m, s


def fmt_dms(d, m, s):
    return f"{d}° {m:02d}′ {s:02d}″"


def fmt_lat(lat):
    d, m, s = dms_parts(lat)
    side = "شمالی" if lat >= 0 else "جنوبی"
    return f"{fmt_dms(d, m, s)} {side}"


def ecl_state(jd, ephe):
    xx = swe.calc_ut(jd, ephe, FLAGS_ECL)[0]
    return xx[0] % 360.0, xx[1], xx[3]


def eq_state(jd, ephe):
    xx = swe.calc_ut(jd, ephe, FLAGS_EQ)[0]
    return xx[0], xx[1], xx[2]  # RA, Dec, فاصله (AU)


# ---------------------------------------------------------------- کواکب

def motion_state(body, speed, factor):
    if not body["wanderer"]:
        return None
    tol = body["tol"] * factor
    if abs(speed) <= tol:
        return dict(key="muqim", name="مقیم", noun="اقامت")
    if speed > 0:
        return dict(key="mustaqim", name="مستقیم", noun="استقامت")
    return dict(key="raji", name="راجع", noun="رجعت")


def calculate_bodies(jd, factor=STATION_DEFAULT_FACTOR):
    rows = []
    for body in BODIES:
        lon, lat, speed = ecl_state(jd, body["ephe"])
        si, d, m, s = lon_to_sign(lon)
        name, symbol, abbr, element = SIGNS[si]
        lat_d, lat_m, lat_s = dms_parts(lat)
        rows.append(dict(
            key=body["key"], name=body["name"], glyph=body["glyph"], color=body["color"],
            wanderer=body["wanderer"], jorm=body["jorm"],
            longitude=lon, latitude=lat, speed=speed,
            sign_index=si, sign_name=name, sign_symbol=symbol, sign_abbr=abbr, element=element,
            dms=fmt_dms(d, m, s), lat_dms=fmt_lat(lat),
            motion=motion_state(body, speed, factor),
            in_scorpio=(si == SCORPIO_INDEX),
        ))
    return rows


# ---------------------------------------------------------------- اتصالات

def calculate_aspects(rows, jorms):
    """
    شروع اتصال: فاصله از نقطه‌ی دقیق ≤ مجموع دو جرم (کوکب‌ها در حال نزدیک شدن).
    ابطال اتصال: پس از دقیق شدن، وقتی بعد حقیقی به نصف مجموع جرمین برسد.
    کوکب سریع‌السیر در نام‌گذاری مقدم می‌شود.
    """
    result = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            p, q = rows[i], rows[j]
            fast, slow = (p, q) if abs(p["speed"]) >= abs(q["speed"]) else (q, p)
            theta = wrap180(slow["longitude"] - fast["longitude"])
            rate = slow["speed"] - fast["speed"]  # تغییر theta در روز
            total = jorms[fast["key"]] + jorms[slow["key"]]

            for asp in ASPECTS:
                a = asp["angle"]
                targets = [0.0] if a == 0 else ([180.0] if a == 180 else [float(a), -float(a)])
                e, target = min(((wrap180(theta - t), t) for t in targets), key=lambda x: abs(x[0]))

                exact = abs(e) < 0.01
                applying = e * rate < 0
                if exact:
                    state, limit = "exact", total
                elif applying and abs(e) <= total:
                    state, limit = "applying", total
                elif (not applying) and abs(e) <= total / 2:
                    state, limit = "separating", total / 2
                else:
                    continue

                hours = None
                if abs(rate) > 1e-6:
                    hours = (-e / rate) * 24.0

                tags = []
                keys = {fast["key"], slow["key"]}
                if keys == {"sun", "moon"}:
                    if asp["key"] == "conj":
                        tags.append("اجتماع")
                    elif asp["key"] == "opp":
                        tags.append("استقبال")
                elif "sun" in keys and asp["key"] == "conj":
                    tags.append("احتراق")
                if asp["key"] != "conj":
                    # ایمن: سریع‌السیر پیش از (طول کمتر از) کندتر؛ ایسر: پس از آن
                    if a == 180:
                        before = ((slow["longitude"] - fast["longitude"]) % 360.0) < 180.0
                    else:
                        before = target > 0
                    tags.append(f"{asp['name']} {'ایمن' if before else 'ایسر'}")

                result.append(dict(
                    type=asp["key"], type_name=asp["name"], glyph=asp["glyph"], angle=asp["angle"],
                    fast=fast, slow=slow, deviation=abs(e), signed_dev=e,
                    state=state, limit=limit, strength=max(0.0, 1.0 - abs(e) / limit) if limit else 0,
                    hours=hours,
                    hours_text=fmt_duration(hours) if hours is not None else "—",
                    tags=tags, pair_keys=f"{fast['key']} {slow['key']}",
                ))
    result.sort(key=lambda a: a["deviation"])
    return result


# ---------------------------------------------------------------- اجتماع

def sun_moon_elongation(jd):
    sl, _, ss = ecl_state(jd, swe.SUN)
    ml, _, ms = ecl_state(jd, swe.MOON)
    return wrap180(ml - sl), ms - ss


def find_conjunction(jd, direction):
    """اجتماع (طول ماه = طول شمس) بعد از jd (direction>0) یا قبل از آن."""
    e, _ = sun_moon_elongation(jd)
    mean_rel = 12.19
    if direction > 0:
        x = jd + ((-e) % 360.0) / mean_rel
    else:
        x = jd - (e % 360.0) / mean_rel
    for _ in range(14):
        e, rate = sun_moon_elongation(x)
        if abs(rate) < 1:
            break
        step = e / rate
        x -= step
        if abs(step) < 1e-7:
            break
    return x


# ---------------------------------------------------------------- افق: غروب‌ها

def _sidereal_deg(jd):
    return swe.sidtime(jd) * 15.0


def altitude(jd, ephe, lat, lon, topocentric=False):
    """ارتفاع هندسی مرکز جرم از افق (درجه)؛ برای ماه با تصحیح اختلاف منظر."""
    ra, dec, dist = eq_state(jd, ephe)
    return _altitude_from(jd, ra, dec, dist, lat, lon, topocentric)


def _altitude_from(jd, ra, dec, dist, lat, lon, topocentric):
    hour_angle = math.radians((_sidereal_deg(jd) + lon - ra) % 360.0)
    phi, delta = math.radians(lat), math.radians(dec)
    sin_h = math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(hour_angle)
    h = math.degrees(math.asin(max(-1.0, min(1.0, sin_h))))
    if topocentric:
        pi = math.asin(6378.14 / (dist * AU_KM))
        h -= math.degrees(math.asin(math.sin(pi) * math.cos(math.radians(h))))
    return h


def _alt_minus_horizon(jd, kind, lat, lon):
    """ارتفاع منهای ارتفاع افق مؤثر (انکسار ۳۴′ + نیم‌قطر)."""
    if kind == "sun":
        ra, dec, dist = eq_state(jd, swe.SUN)
        return _altitude_from(jd, ra, dec, dist, lat, lon, False) - (-0.8333)
    ra, dec, dist = eq_state(jd, swe.MOON)
    semi = math.degrees(math.asin(1737.4 / (dist * AU_KM)))
    return _altitude_from(jd, ra, dec, dist, lat, lon, True) - (-(34.0 / 60.0 + semi))


def find_sets(kind, jd_start, jd_end, lat, lon, step=1.0 / 144.0):
    """زمان‌های غروب (عبور رو به پایین از افق) در بازه."""
    sets = []
    t = jd_start
    prev = _alt_minus_horizon(t, kind, lat, lon)
    while t < jd_end:
        nxt = min(t + step, jd_end)
        cur = _alt_minus_horizon(nxt, kind, lat, lon)
        if prev > 0 >= cur:
            lo, hi = t, nxt
            for _ in range(40):
                mid = (lo + hi) / 2
                if _alt_minus_horizon(mid, kind, lat, lon) > 0:
                    lo = mid
                else:
                    hi = mid
            sets.append((lo + hi) / 2)
        t, prev = nxt, cur
    return sets


def sunset_jd(city, local_date):
    start = datetime(local_date.year, local_date.month, local_date.day, tzinfo=IRAN_TZ)
    j0 = to_jd(start)
    s = find_sets("sun", j0, j0 + 1.0, city["lat"], city["lon"])
    return s[0] if s else None


def moonset_near(city, jd_ref):
    sets = find_sets("moon", jd_ref - 0.75, jd_ref + 0.75, city["lat"], city["lon"])
    if not sets:
        return None
    return min(sets, key=lambda t: abs(t - jd_ref))


def classify_evening(elong, lag_deg, crit=None):
    """حکم رؤیت بر پایه‌ی جدول خواجه نصیرالدین طوسی؛ (سطح، برچسب کوتاه، متن)."""
    crit = crit or DEFAULT_CRITERIA
    t, smin, low = crit["tiers"], crit["sawa_min"], crit["low_maadal"]
    if elong < 0:
        return "before", "قبل از مقارنه", "ماه هنوز به خورشید نرسیده است و هلال دیده نمی‌شود."
    if lag_deg is None or lag_deg <= 0:
        return "no", "غیرممکن", "ماه پیش از خورشید (یا همزمان) غروب می‌کند؛ رؤیت هلال ممکن نیست."
    if elong >= smin:
        if lag_deg < t[0]:
            return "unlikely", "رؤیت بعید", (f"بعد سواء بیش از {smin:g} درجه است، اما بعد معدل کمتر از "
                                              f"{t[0]:g} درجه است؛ پایین‌تر از حد جدول خواجه نصیرالدین طوسی در زیج ایلخانی و رؤیت بعید است.")
        label = TIER_LABELS[-1]
        for i in range(1, 5):
            if lag_deg < t[i]:
                label = TIER_LABELS[i - 1]
                break
        return "possible", label, f"طبق جدول خواجه نصیرالدین طوسی در زیج ایلخانی (بعد سواء بیش از {smin:g} درجه و بعد معدل در این محدوده)."
    if lag_deg >= low:
        return "possible", "رؤیت‌پذیر", (f"بعد سواء کمتر از {smin:g} درجه است، اما بعد معدل حدود {low:g} درجه "
                                          "یا بیشتر است؛ طبق جدول خواجه نصیرالدین طوسی در زیج ایلخانی رؤیت‌پذیر است.")
    return "unlikely", "رؤیت بعید", (f"بعد سواء کمتر از {smin:g} درجه و بعد معدل کمتر از {low:g} درجه است؛ "
                                      "رؤیت هلال بعید است.")


def evening_report(city, local_date, crit=None):
    """بعد سواء و بعد معدل در غروب خورشید برای یک شهر و یک روز محلی."""
    sj = sunset_jd(city, local_date)
    if sj is None:
        return None
    sun_lon, _, _ = ecl_state(sj, swe.SUN)
    moon_lon, moon_lat, _ = ecl_state(sj, swe.MOON)
    elong = wrap180(moon_lon - sun_lon)

    mj = moonset_near(city, sj)
    lag_min = (mj - sj) * 1440.0 if mj is not None else None

    moon_alt = altitude(sj, swe.MOON, city["lat"], city["lon"], topocentric=True)
    last_conj = find_conjunction(sj, -1)
    next_conj = find_conjunction(sj, +1)
    status, verdict, text = classify_evening(elong, lag_min / 4.0 if lag_min is not None else None, crit)

    return dict(
        date=local_date, sunset=from_jd(sj), moonset=from_jd(mj) if mj is not None else None,
        elong=elong, abs_elong=abs(elong), moon_lat=moon_lat, moon_alt=moon_alt,
        lag_min=lag_min, lag_deg=(lag_min / 4.0 if lag_min is not None else None),
        age_hours=(sj - last_conj) * 24.0, hours_to_next=(next_conj - sj) * 24.0,
        status=status, verdict=verdict, status_text=text,
        sunset_text=fmt_hm(from_jd(sj)), moonset_text=fmt_hm(from_jd(mj)) if mj is not None else "—",
        sunset_short=from_jd(sj).astimezone(IRAN_TZ).strftime("%H:%M"),
        moonset_short=from_jd(mj).astimezone(IRAN_TZ).strftime("%H:%M") if mj is not None else "—",
    )


# ---------------------------------------------------------------- نمایش ماه

def moon_phase_shape(elong):
    """پارامترهای مسیر SVG برای شکل ماه (هلال/بدر) بر پایه‌ی بعد سواء علامت‌دار."""
    c = math.cos(math.radians(elong))
    return dict(
        rx=round(50 * abs(c), 2),
        sweep=0 if c > 0 else 1,
        waning=elong < 0,
        illumination=round((1 - c) / 2 * 100, 1),
    )


# ---------------------------------------------------------------- تجمیع

def build_analysis(dt_utc, city_key, jorms, factor, crit=None):
    city = CITIES.get(city_key, CITIES[DEFAULT_CITY])
    jd = to_jd(dt_utc)
    rows = calculate_bodies(jd, factor)
    aspects = calculate_aspects(rows, jorms)

    local = dt_utc.astimezone(IRAN_TZ)
    evening = evening_report(city, local.date(), crit)

    elong_now, _ = sun_moon_elongation(jd)
    sun_alt = altitude(jd, swe.SUN, city["lat"], city["lon"])
    moon_alt = altitude(jd, swe.MOON, city["lat"], city["lon"], topocentric=True)
    last_conj = find_conjunction(jd, -1)
    next_conj = find_conjunction(jd, +1)

    # جدول شب‌های استهلال پیرامون نزدیک‌ترین اجتماع مرتبط
    ref_conj = last_conj if (jd - last_conj) < 3.0 else next_conj
    ref_date = from_jd(ref_conj).astimezone(IRAN_TZ).date()
    evenings = []
    for k in range(3):
        d = ref_date + timedelta(days=k)
        rep = evening if d == local.date() and evening else evening_report(city, d, crit)
        if rep:
            rep = dict(rep, is_selected=(d == local.date()))
            evenings.append(rep)

    alerts = build_alerts(jd, elong_now, last_conj, next_conj, evening)

    return dict(
        city=city, rows=rows, aspects=aspects, evening=evening, evenings=evenings,
        elong_now=elong_now, sun_alt=sun_alt, moon_alt=moon_alt,
        last_conj=from_jd(last_conj), next_conj=from_jd(next_conj),
        phase=moon_phase_shape(evening["elong"] if evening else elong_now),
        phase_now=moon_phase_shape(elong_now),
        alerts=alerts, ref_conj=from_jd(ref_conj), crit=crit or DEFAULT_CRITERIA,
    )


def build_alerts(jd, elong_now, last_conj, next_conj, evening):
    alerts = []
    to_next_h = (next_conj - jd) * 24.0
    since_h = (jd - last_conj) * 24.0

    if min(to_next_h, since_h) < 0.5:
        alerts.append(("info", "لحظه‌ی اجتماع",
                       "زمان واردشده تقریباً همزمان با مقارنه‌ی شمس و قمر (اجتماع) است."))
    elif to_next_h <= 48:
        alerts.append(("warn", "پیش از مقارنه",
                       f"اجتماع شمس و قمر {fmt_duration(to_next_h)} دیگر رخ می‌دهد "
                       f"({fmt_local(from_jd(next_conj))} به وقت ایران)؛ تا آن زمان هلال دیده نمی‌شود."))
    elif since_h <= 72:
        alerts.append(("good", "پس از مقارنه",
                       f"{fmt_duration(since_h)} از اجتماع گذشته است ({fmt_local(from_jd(last_conj))}). "
                       "غروب‌های این روزها، زمان استهلال هلال است."))

    if evening and (-30 <= evening["elong"] <= 40):
        level = {"before": "warn", "no": "danger", "unlikely": "warn", "possible": "good"}[evening["status"]]
        alerts.append((level, "غروب همین روز در افق انتخابی", f'{evening["verdict"]}: {evening["status_text"]}'))
    return alerts
