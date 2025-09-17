#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل اصلی اجرای پروژه فردوسی حسینی
"""

from app import create_app

# استفاده از محیط development برای اجرای لوکال
#app = create_app('development')
app = create_app('development')

# برای اجرا در سرور
# app = create_app('production')

if __name__ == '__main__':
    app.run()
    #app.run(debug=True, host='127.0.0.1', port=5000)