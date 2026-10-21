
from datetime import datetime, timedelta, timezone
from pathlib import Path

import swisseph as swe

# همان مسیر اپمریس استفاده‌شده در برنامه Flask
EPHE_PATH = Path(__file__).resolve().parent.parent / "app" / "ephe"
swe.set_ephe_path(str(EPHE_PATH))

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

# بازه سال ۱۴۰۵ شمسی:
# شروع: ۱ فروردین ۱۴۰۵
# پایان: آخرین لحظه ۲۹ اسفند ۱۴۰۵
# معادل تقریبی میلادی: 2026-03-21 تا 2027-03-20
START_UTC = datetime(2026, 3, 20, 20, 30, tzinfo=timezone.utc)
END_UTC = datetime(2027, 3, 20, 20, 30, tzinfo=timezone.utc)

# مرزهای برج عقرب در زودیاک مورد استفاده کد فعلی
SCORPIO_START = 210.0
SCORPIO_END = 240.0

def julian_day(dt):
    hour = dt.hour + dt.minute / 60 + dt.second / 3600
    return swe.julday(dt.year, dt.month, dt.day, hour)



def moon_longitude(dt):
    result = swe.calc_ut(julian_day(dt), swe.MOON)
    positions = result[0]
    return positions[0] % 360



def find_crossing(left, right, target):
    """پیدا کردن زمان عبور ماه از یک مرز طول جغرافیایی با دقت ثانیه."""
    for _ in range(45):
        middle = left + (right - left) / 2
        longitude = moon_longitude(middle)

        # اختلاف زاویه‌ای علامت‌دار نسبت به مرز هدف
        delta = ((longitude - target + 180) % 360) - 180

        if delta < 0:
            left = middle
        else:
            right = middle

    return left + (right - left) / 2

def find_events():
    events = []
    step = timedelta(hours=1)
    current = START_UTC
    previous_lon = moon_longitude(current)
    previous_unwrapped = previous_lon

    while current < END_UTC:
        next_time = min(current + step, END_UTC)
        next_lon = moon_longitude(next_time)

        # باز کردن پرش ۳۶۰ به صفر
        delta = ((next_lon - previous_lon + 180) % 360) - 180
        next_unwrapped = previous_unwrapped + delta

        # بررسی عبور از مرز ورود یا خروج
        for target, label in (
            (SCORPIO_START, "ورود به عقرب"),
            (SCORPIO_END, "خروج از عقرب"),
        ):
            k_min = int((previous_unwrapped - target) // 360) - 1
            k_max = int((next_unwrapped - target) // 360) + 1

            for k in range(k_min, k_max + 1):
                boundary = target + 360 * k

                if previous_unwrapped < boundary <= next_unwrapped:
                    event_time = find_crossing(current, next_time, target)
                    events.append((event_time, label))

        current = next_time
        previous_lon = next_lon
        previous_unwrapped = next_unwrapped

    return sorted(events, key=lambda item: item[0])

def main():
    if not EPHE_PATH.exists():
        raise FileNotFoundError(
            f"پوشه اپمریس پیدا نشد: {EPHE_PATH}"
        )

    print(f"مسیر اپمریس: {EPHE_PATH}")
    print("رویدادهای ورود و خروج ماه از برج عقرب")
    print("-" * 72)

    for utc_time, event in find_events():
        iran_time = utc_time.astimezone(IRAN_TZ)

        print(
            f"{event:15} | "
            f"ایران: {iran_time:%Y-%m-%d %H:%M:%S} | "
            f"UTC: {utc_time:%Y-%m-%d %H:%M:%S}"
        )

if __name__ == "__main__":
    main()
