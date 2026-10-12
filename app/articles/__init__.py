# -*- coding: utf-8 -*-
"""
app/articles/__init__.py

تنها نقطه‌ی اتصال این ماژول به بقیه‌ی پروژه. کافی‌ست در app/routes/__init__.py
این یک تابع را صدا بزنید (به INSTALL.md نگاه کنید) - هیچ فایل دیگری از
پروژه نیازی به تغییر ندارد.
"""


def register_articles(app):
    """دو بلوپرینت (عمومی و مدیریت) ماژول مقالات را روی app ثبت می‌کند."""
    from app.articles.routes_public import public_bp
    from app.articles.routes_admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
