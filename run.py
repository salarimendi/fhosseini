#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل اصلی اجرای پروژه فردوسی حسینی
"""

from app import create_app

# استفاده از محیط development برای اجرای لوکال
app = create_app('development')

if __name__ == '__main__':
    app.run()