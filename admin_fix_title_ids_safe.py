#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت امن بازشماری ID های جدول titles
و همگام‌سازی title_id در جداول وابسته

ویژه SQLite – بدون DROP TABLE – بدون migration
"""

import sqlite3
import shutil
import os
from datetime import datetime
from pathlib import Path


OFFSET = 100000  # عدد امن برای جلوگیری از برخورد ID ها


class TitleIDFixerSafe:
    """
    این کلاس:
    1) ID های titles را بر اساس (garden, order_in_garden) مرتب می‌کند
    2) ابتدا ID ها را به بازه موقت منتقل می‌کند (OFFSET)
    3) سپس ID نهایی را اعمال می‌کند
    4) بعد title_id در verses / comments / recordings را اصلاح می‌کند
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.backup_path = None
        self.id_mapping = {}      # old_id -> new_id
        self.temp_mapping = {}    # old_id -> temp_id

    # ------------------------------
    # ابزارهای کمکی
    # ------------------------------

    def connect(self):
        """ایجاد اتصال به دیتابیس"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def backup(self):
        """تهیه نسخه پشتیبان از دیتابیس"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.db_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        self.backup_path = backup_dir / f"backup_{ts}.db"
        shutil.copy2(self.db_path, self.backup_path)
        print(f"✓ بکاپ ساخته شد: {self.backup_path}")

    # ------------------------------
    # مرحله 1: ساخت mapping نهایی
    # ------------------------------

    def build_id_mapping(self):
        """
        old_id → new_id
        new_id بر اساس garden و order_in_garden
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, garden, order_in_garden
            FROM titles
            ORDER BY garden, order_in_garden
        """)

        rows = cur.fetchall()
        for new_id, row in enumerate(rows, start=1):
            old_id = row["id"]
            self.id_mapping[old_id] = new_id
            self.temp_mapping[old_id] = old_id + OFFSET

        conn.close()

        print(f"✓ نقشه ID ساخته شد ({len(self.id_mapping)} عنوان)")

    # ------------------------------
    # مرحله 2: انتقال ID ها به بازه موقت
    # ------------------------------

    def move_titles_to_temp_ids(self, cur):
        """
        titles.id → id + OFFSET
        """
        for old_id, temp_id in self.temp_mapping.items():
            cur.execute(
                "UPDATE titles SET id = ? WHERE id = ?",
                (temp_id, old_id)
            )

    def update_fk_to_temp(self, cur):
        """
        title_id در جداول وابسته → temp_id
        """
        for old_id, temp_id in self.temp_mapping.items():
            cur.execute(
                "UPDATE verses SET title_id = ? WHERE title_id = ?",
                (temp_id, old_id)
            )
            cur.execute(
                "UPDATE comments SET title_id = ? WHERE title_id = ?",
                (temp_id, old_id)
            )
            cur.execute(
                "UPDATE recordings SET title_id = ? WHERE title_id = ?",
                (temp_id, old_id)
            )

    # ------------------------------
    # مرحله 3: اعمال ID نهایی
    # ------------------------------

    def apply_final_ids(self, cur):
        """
        temp_id → new_id
        """
        for old_id, new_id in self.id_mapping.items():
            temp_id = self.temp_mapping[old_id]

            # titles
            cur.execute(
                "UPDATE titles SET id = ? WHERE id = ?",
                (new_id, temp_id)
            )

            # verses
            cur.execute(
                "UPDATE verses SET title_id = ? WHERE title_id = ?",
                (new_id, temp_id)
            )

            # comments
            cur.execute(
                "UPDATE comments SET title_id = ? WHERE title_id = ?",
                (new_id, temp_id)
            )

            # recordings
            cur.execute(
                "UPDATE recordings SET title_id = ? WHERE title_id = ?",
                (new_id, temp_id)
            )

    # ------------------------------
    # اجرای کل فرآیند
    # ------------------------------

    def run(self):
        if not os.path.exists(self.db_path):
            print("✗ فایل دیتابیس وجود ندارد")
            return

        self.backup()
        self.build_id_mapping()

        conn = self.connect()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN")

            # 1️⃣ انتقال ID ها به بازه موقت
            self.move_titles_to_temp_ids(cur)
            self.update_fk_to_temp(cur)

            # 2️⃣ اعمال ID نهایی
            self.apply_final_ids(cur)

            conn.commit()
            print("✓ بازشماری ID ها با موفقیت انجام شد")

        except Exception as e:
            conn.rollback()
            print("✗ خطا رخ داد، عملیات rollback شد")
            print(e)

        finally:
            conn.close()


# ------------------------------
# اجرای مستقیم فایل
# ------------------------------

if __name__ == "__main__":
    print("\n=== اصلاح امن ID های جدول titles ===\n")

    default_db = "instance/ferdowsi_hosseini.db"
    db_path = input(f"مسیر دیتابیس [{default_db}]: ").strip()
    if not db_path:
        db_path = default_db

    fixer = TitleIDFixerSafe(db_path)
    fixer.run()

    input("\nبرای خروج Enter بزنید...")
