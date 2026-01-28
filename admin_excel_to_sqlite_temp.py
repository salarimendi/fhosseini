import sqlite3
import pandas as pd

# =========================
# تنظیمات
# =========================
EXCEL_FILE = 'poems.xlsx'
SQLITE_DB = 'ferdosi.db'
SHEET_NAME = 0  # یا نام شیت

# =========================
# اتصال دیتابیس
# =========================
conn = sqlite3.connect(SQLITE_DB)
cur = conn.cursor()

# =========================
# ساخت جداول temp
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS titles_temp (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    garden INTEGER NOT NULL,
    order_in_garden INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS verses_temp (
    id INTEGER PRIMARY KEY,
    title_id INTEGER NOT NULL,
    order_in_title INTEGER NOT NULL,
    verse_1 TEXT NOT NULL,
    verse_2 TEXT,
    variant_diff TEXT,
    present_in_versions TEXT,
    is_subtitle INTEGER NOT NULL
)
""")

conn.commit()

# =========================
# خواندن اکسل
# =========================
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

# =========================
# متغیرهای کنترلی
# =========================
current_title_id = None
current_order_in_title = 0

current_garden = 0
order_in_garden = 0

next_title_id = 1
next_verse_id = 1

# =========================
# پردازش سطر به سطر
# =========================
for idx, row in df.iterrows():
    control = row[0]
    col_b = str(row[1]).strip() if not pd.isna(row[1]) else None
    col_c = str(row[2]).strip() if not pd.isna(row[2]) else None
    diff = str(row[3]).strip() if not pd.isna(row[3]) else None
    present = str(row[4]).strip() if not pd.isna(row[4]) else None

    # --- شروع باغ جدید ---
    if control == 3:
        current_garden += 1
        order_in_garden = 0
        continue

    # --- تیتر اصلی ---
    if control == 1 and col_b:
        order_in_garden += 1
        current_order_in_title = 0

        cur.execute("""
        INSERT INTO titles_temp (id, title, garden, order_in_garden)
        VALUES (?, ?, ?, ?)
        """, (
            next_title_id,
            col_b,
            current_garden,
            order_in_garden
        ))

        current_title_id = next_title_id
        next_title_id += 1
        continue

    # --- بیت یا تیتر فرعی ---
    if current_title_id is None:
        continue  # هنوز تیتر نداریم

    # بیت
    if pd.isna(control):
        if not col_b:
            continue

        current_order_in_title += 1

        cur.execute("""
        INSERT INTO verses_temp
        (id, title_id, order_in_title, verse_1, verse_2,
         variant_diff, present_in_versions, is_subtitle)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            next_verse_id,
            current_title_id,
            current_order_in_title,
            col_b,
            col_c,
            diff,
            present
        ))

        next_verse_id += 1
        continue

    # تیتر فرعی
    if control == 2 and col_b:
        current_order_in_title += 1

        cur.execute("""
        INSERT INTO verses_temp
        (id, title_id, order_in_title, verse_1, verse_2,
         variant_diff, present_in_versions, is_subtitle)
        VALUES (?, ?, ?, ?, NULL, ?, ?, 1)
        """, (
            next_verse_id,
            current_title_id,
            current_order_in_title,
            col_b,
            diff,
            present
        ))

        next_verse_id += 1
        continue

    # سایر موارد → نادیده گرفته می‌شود

# =========================
# پایان
# =========================
conn.commit()
conn.close()

print("✅ انتقال داده‌ها به جداول temp با موفقیت انجام شد.")
