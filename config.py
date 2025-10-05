#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل تنظیمات پروژه فردوسی حسینی
"""

import os
from pathlib import Path
from datetime import timedelta, UTC

# مسیر اصلی پروژه
basedir = Path(__file__).resolve().parent

class Config:
    """تنظیمات پایه"""
    
    # تنظیمات امنیتی
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'your-csrf-secret-key'
    
    # تنظیمات Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "redis://localhost:6379/0"  # استفاده از Redis برای ذخیره‌سازی
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"  # محدودیت پیش‌فرض
    RATELIMIT_LOGIN = "5 per minute"  # محدودیت برای لاگین
    RATELIMIT_HEADERS_ENABLED = True
    
    # تنظیمات هدرهای امنیتی
    SECURE_HEADERS = {
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline';",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block'
    }
    
    # تنظیمات پایگاه داده
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "instance", "ferdosi.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات فایل آپلود
    UPLOAD_MAX_SIZE_MB = 11  # تنظیم حجم مجاز فایل به مگابایت
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or \
        os.path.join(basedir, 'uploads')  # مسیر نسبی ./uploads/
    MAX_CONTENT_LENGTH = UPLOAD_MAX_SIZE_MB * 1024 * 1024  # تبدیل به بایت
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
    
    # تنظیمات تصاویر پژوهشی
    RESEARCH_IMAGE_UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'research_images')
    RESEARCH_IMAGE_MAX_SIZE_MB = 5  # حجم به مگابایت
    RESEARCH_IMAGE_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    

    # تنظیمات Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # تنظیمات ایمیل
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # تنظیمات سایت
    SITE_NAME = 'فردوسی حسینی'
    SITE_URL = os.environ.get('SITE_URL', 'https://ferdowsihosseini.ir')
    INSTAGRAM_URL = 'https://instagram.com/ferdowsihosseini'
    TELEGRAM_URL = 'https://t.me/ferdowsihosseini'
    
    # تنظیمات جستجو
    SEARCH_RESULTS_PER_PAGE = 10
    
    # تنظیمات سایت
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    @staticmethod
    def init_app(app):
        """اعمال تنظیمات روی اپلیکیشن"""
        # ایجاد پوشه آپلود در صورت عدم وجود
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # ایجاد پوشه instance در صورت عدم وجود
        os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

    @staticmethod
    def get_upload_max_size_formatted():
        """دریافت حجم مجاز فایل به صورت فرمت شده"""
        return f"{Config.UPLOAD_MAX_SIZE_MB}M"

class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    # در محیط توسعه از مسیر نسبی استفاده می‌کنیم
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "instance", "ferdosi.db")}'
    PREFERRED_URL_SCHEME = 'http'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    # استفاده صریح از حافظه برای rate-limit تا هشدار Redis نمایش داده نشود
    RATELIMIT_STORAGE_URL = "memory://"
    
    # تنظیمات Rate Limiting برای محیط توسعه - محدودیت بسیار کم برای تست راحت‌تر
    RATELIMIT_DEFAULT = "5000 per day;1000 per hour;200 per minute"  # محدودیت بسیار کم برای توسعه
    RATELIMIT_LOGIN = "100 per minute"  # محدودیت بسیار کم برای لاگین در توسعه

class ProductionConfig(Config):
    """تنظیمات محیط تولید"""
    DEBUG = False
    
    # در محیط تولید از مسیر مطلق استفاده می‌کنیم
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:////home/qouyvwti/myflaskapp/instance/ferdosi.db'
    
    # تنظیمات مسیرها در محیط تولید - استفاده از مسیر نسبی برای آپلود
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    LOG_FOLDER = '/home/qouyvwti/myflaskapp/logs'
    
    # تنظیمات SSL برای محیط تولید
    PREFERRED_URL_SCHEME = 'https'
    
    # تنظیمات Rate Limiting برای محیط تولید - محدودیت متعادل برای امنیت و کارایی
    RATELIMIT_DEFAULT = "500 per day;100 per hour;20 per minute"  # محدودیت متعادل برای تولید
    RATELIMIT_LOGIN = "10 per minute"  # محدودیت متعادل برای لاگین در تولید
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # تنظیمات لاگ برای محیط تولید
        import logging
        from logging.handlers import RotatingFileHandler
        
        # ایجاد پوشه logs در صورت عدم وجود
        if not os.path.exists(cls.LOG_FOLDER):
            os.makedirs(cls.LOG_FOLDER, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            os.path.join(cls.LOG_FOLDER, 'ferdowsi_hosseini.log'),
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Ferdowsi Hosseini startup')

class TestingConfig(Config):
    """تنظیمات محیط تست"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # استفاده از دیتابیس موقت در حافظه
    WTF_CSRF_ENABLED = False  # غیرفعال کردن CSRF برای تست‌ها
    SERVER_NAME = 'localhost:5000'  # تنظیم نام سرور برای تست‌ها
    PREFERRED_URL_SCHEME = 'http'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # تنظیمات Rate Limiting برای محیط تست - محدودیت بسیار کم برای تست‌ها
    RATELIMIT_DEFAULT = "10000 per day;1000 per hour;100 per minute"  # محدودیت بسیار کم برای تست
    RATELIMIT_LOGIN = "100 per minute"  # محدودیت بسیار کم برای لاگین در تست

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}