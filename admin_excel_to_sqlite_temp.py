import sqlite3
import pandas as pd

# =========================
# تنظیمات
# =========================
EXCEL_FILE = 'temp/poems.xlsx'
SQLITE_DB = 'temp/ferdosi.db'
SHEET_NAME = 'all'

# =========================
# اتصال دیتابیس
# =========================
conn = sqlite3.connect(SQLITE_DB)
cur = conn.cursor()


# =========================
# حذف جداول اصلی
# =========================

cur.execute("DROP TABLE IF EXISTS verses;")
cur.execute("DROP TABLE IF EXISTS titles;")

conn.commit()

# =========================
# ساخت جداول temp
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS titles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    garden INTEGER NOT NULL,
    order_in_garden INTEGER NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY,
    title_id INTEGER NOT NULL,
    order_in_title INTEGER NOT NULL,
    verse_1 TEXT NOT NULL,
    verse_2 TEXT,
    variant_diff TEXT NOT NULL,
    present_in_versions TEXT NOT NULL,
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

current_garden = 1
order_in_garden = 0


next_title_id = 1
next_verse_id = 1

# =========================
# پردازش سطر به سطر
# =========================
for idx, row in df.iterrows():
    control = row.iloc[0]

    col_b = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else ''
    col_c = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else ''
    col_d = str(row.iloc[3]).strip() if not pd.isna(row.iloc[3]) else ''
    col_e = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else ''

    # --- پایان فایل ---
    if control == 4:
        print(f"⛔ پایان پردازش در سطر {idx + 1}")
        break

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
        INSERT INTO titles (id, title, garden, order_in_garden)
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

    # اگر هنوز تیتر نداریم
    if current_title_id is None:
        continue

    # --- بیت ---
    if pd.isna(control):
        if not col_b:
            continue

        current_order_in_title += 1

        cur.execute("""
        INSERT INTO verses
        (id, title_id, order_in_title, verse_1, verse_2,
         variant_diff, present_in_versions, is_subtitle)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            next_verse_id,
            current_title_id,
            current_order_in_title,
            col_b,
            col_c,
            col_d,
            col_e
        ))

        next_verse_id += 1
        continue

    # --- تیتر فرعی ---
    if control == 2 and col_d:
        current_order_in_title += 1

        cur.execute("""
        INSERT INTO verses
        (id, title_id, order_in_title, verse_1, verse_2,
         variant_diff, present_in_versions, is_subtitle)
        VALUES (?, ?, ?, ?, '', '', ?, 1)
        """, (
            next_verse_id,
            current_title_id,
            current_order_in_title,
            col_d,
            col_e
        ))

        next_verse_id += 1
        continue

    # سایر مقادیر control → نادیده گرفته می‌شود

# =========================
# پایان
# =========================
conn.commit()
conn.close()

print("✅ انتقال داده‌ها با نسخه نهایی یکپارچه با موفقیت انجام شد.")
