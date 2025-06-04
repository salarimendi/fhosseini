#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل اصلی اپلیکیشن فردوسی حسینی
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import config

# ایجاد نمونه‌های اصلی
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()

def create_app(config_name=None):
    """ایجاد و تنظیم اپلیکیشن Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # اطمینان از وجود پوشه instance
    os.makedirs(app.instance_path, exist_ok=True)
    

    # راه‌اندازی افزونه‌ها
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # راه‌اندازی Rate Limiter
    limiter.init_app(app)
    
    # راه‌اندازی Talisman با تنظیمات امنیتی
    talisman.init_app(app,
                     force_https=True,
                     strict_transport_security=True,
                     strict_transport_security_max_age=31536000,
                     strict_transport_security_include_subdomains=True,
                     session_cookie_secure=True,
                     content_security_policy={
                         'default-src': "'self'",
                         'img-src': ["'self'", 'data:', 'https:'],
                         'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
                         'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
                         'font-src': ["'self'", 'https://cdnjs.cloudflare.com']
                     })
    
    # تنظیمات Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # ثبت Blueprintها
    from app.routes.main import main_bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.auth import auth_bp as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.verses import verses_bp as verses_blueprint
    app.register_blueprint(verses_blueprint, url_prefix='/verses')
    
    from app.routes.admin import admin_bp as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from app.routes.comments import comments_bp as comments_blueprint
    app.register_blueprint(comments_blueprint, url_prefix='/comments')
    
    # ایجاد جداول پایگاه داده
    with app.app_context():
        db.create_all()
        
        # ایجاد کاربر مدیر پیش‌فرض در صورت عدم وجود
        from app.models import User
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@ferdowsihosseini.ir',
                fullname='مدیر سایت',
                role='admin'
            )
            admin_user.set_password('admin123')  # رمز پیش‌فرض - باید تغییر کند
            db.session.add(admin_user)
            db.session.commit()
    
    # متغیرهای Template سراسری
    @app.context_processor
    def inject_config():
        return {
            'SITE_NAME': app.config['SITE_NAME'],
            'INSTAGRAM_URL': app.config['INSTAGRAM_URL'],
            'TELEGRAM_URL': app.config['TELEGRAM_URL']
        }
    
    # فیلتر Jinja2 برای فارسی
    @app.template_filter('persian_number')
    def persian_number_filter(number):
        """تبدیل اعداد انگلیسی به فارسی"""
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        result = str(number)
        for i, digit in enumerate(english_digits):
            result = result.replace(digit, persian_digits[i])
        return result
    
    return app