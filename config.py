#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل تنظیمات پروژه فردوسی حسینی
"""

import os
from decouple import config as env_config

from pathlib import Path
from datetime import timedelta, UTC

# مسیر اصلی پروژه
basedir = Path(__file__).resolve().parent

class Config:
    """تنظیمات پایه"""
    
    # تنظیمات امنیتی
    SECRET_KEY = env_config('SECRET_KEY', default='dev-key-123')
    WTF_CSRF_SECRET_KEY = env_config('WTF_CSRF_SECRET_KEY', default='your-csrf-secret-key')
    
    # تنظیمات Rate Limiting
    RATELIMIT_ENABLED = env_config('RATELIMIT_ENABLED', cast=bool, default=True)
    RATELIMIT_STORAGE_URL = env_config('RATELIMIT_STORAGE_URL', default='redis://localhost:6379/0')
    RATELIMIT_DEFAULT = env_config('RATELIMIT_DEFAULT', default='200 per day;50 per hour;10 per minute')
    RATELIMIT_LOGIN = env_config('RATELIMIT_LOGIN', default='5 per minute')
    RATELIMIT_HEADERS_ENABLED = env_config('RATELIMIT_HEADERS_ENABLED', cast=bool, default=True)
    
    # تنظیمات هدرهای امنیتی
    SECURE_HEADERS = {
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline';",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block'
    }
    
    # تنظیمات پایگاه داده
    SQLALCHEMY_DATABASE_URI = env_config(
        'DATABASE_URL',
        default=f'sqlite:///{os.path.join(basedir, "instance", "ferdosi.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات فایل آپلود
    UPLOAD_MAX_SIZE_MB = env_config('UPLOAD_MAX_SIZE_MB', cast=int, default=11)  # تنظیم حجم مجاز فایل به مگابایت  
    UPLOAD_FOLDER = env_config('UPLOAD_FOLDER', default=os.path.join(basedir, 'uploads'))  # مسیر نسبی ./uploads/
    MAX_CONTENT_LENGTH = UPLOAD_MAX_SIZE_MB * 1024 * 1024  # تبدیل به بایت
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
    
    # تنظیمات تصاویر پژوهشی
    RESEARCH_IMAGE_UPLOAD_FOLDER = env_config('RESEARCH_IMAGE_UPLOAD_FOLDER', default=os.path.join(basedir, 'uploads', 'research_images'))
    RESEARCH_IMAGE_MAX_SIZE_MB = env_config('RESEARCH_IMAGE_MAX_SIZE_MB', cast=int, default=5)  # حجم به مگابایت
    RESEARCH_IMAGE_ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    
 
    # تنظیمات Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # تنظیمات ایمیل
    MAIL_SERVER = env_config('MAIL_SERVER', default='smtp.gmail.com')
    MAIL_PORT = env_config('MAIL_PORT', cast=int, default=587)
    MAIL_USE_TLS = env_config('MAIL_USE_TLS', cast=bool, default=True)
    MAIL_USERNAME = env_config('MAIL_USERNAME', default='')
    MAIL_PASSWORD = env_config('MAIL_PASSWORD', default='')
    MAIL_DEFAULT_SENDER = env_config('MAIL_DEFAULT_SENDER', default='')
    
    # تنظیمات سایت
    SITE_NAME = env_config('SITE_NAME', default='فردوسی حسینی')
    SITE_URL = env_config(
        'SITE_URL',
        default='https://ferdowsihosseini.ir'
    )
    INSTAGRAM_URL = env_config(
        'INSTAGRAM_URL',
        default='https://instagram.com/ferdowsihosseini'
    )
    TELEGRAM_URL = env_config(
        'TELEGRAM_URL',
        default='https://t.me/ferdowsihosseini'
    )
    
    # تنظیمات جستجو
    SEARCH_RESULTS_PER_PAGE = env_config('SEARCH_RESULTS_PER_PAGE', cast=int, default=10)
    
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

    @classmethod
    def get_upload_max_size_formatted(cls):
        """دریافت حجم مجاز فایل به صورت فرمت شده"""
        return f"{cls.UPLOAD_MAX_SIZE_MB}M"

class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    # در محیط توسعه از مسیر نسبی استفاده می‌کنیم
    SQLALCHEMY_DATABASE_URI = env_config(
        'DATABASE_URL',
        default=f'sqlite:///{os.path.join(basedir, "instance", "ferdosi.db")}')
    PREFERRED_URL_SCHEME = 'http'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    # استفاده صریح از حافظه برای rate-limit تا هشدار Redis نمایش داده نشود
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # تنظیمات Rate Limiting برای محیط توسعه - محدودیت بسیار کم برای تست راحت‌تر
    RATELIMIT_DEFAULT = "5000 per day;1000 per hour;200 per minute"  # محدودیت بسیار کم برای توسعه
    RATELIMIT_LOGIN = "100 per minute"  # محدودیت بسیار کم برای لاگین در توسعه

class ProductionConfig(Config):
    """تنظیمات محیط تولید"""
    DEBUG = False
    
    # در محیط تولید از مسیر مطلق استفاده می‌کنیم
    SQLALCHEMY_DATABASE_URI = env_config(
        'DATABASE_URL',
        default=f'sqlite:///{os.path.join(basedir, "instance", "ferdosi.db")}')
    
    # تنظیمات مسیرها در محیط تولید - استفاده از مسیر نسبی برای آپلود
    UPLOAD_FOLDER = env_config(
        'UPLOAD_FOLDER',
        default=os.path.join(basedir, 'uploads'))
    LOG_FOLDER = env_config(
        'LOG_FOLDER',
        default=os.path.join(basedir, 'logs'))
    
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
    RATELIMIT_LOGIN = "5 per minute"  # محدودیت بسیار کم برای لاگین در تست

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}