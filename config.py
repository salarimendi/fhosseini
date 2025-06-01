#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل تنظیمات پروژه فردوسی حسینی
"""

import os
from pathlib import Path
from datetime import timedelta

# مسیر اصلی پروژه

basedir = Path(__file__).resolve().parent
print(f"Base directory: {basedir}")




class Config:
    """تنظیمات پایه"""
    
    db_path = basedir / "instance" / "ferdosi.db"
    print(f"Database path: {db_path}")
    
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    print(f"Database URI: {SQLALCHEMY_DATABASE_URI}")


    # تنظیمات امنیتی
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ferdowsi-hosseini-secret-key-2025'
    
    # تنظیمات پایگاه داده
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/ferdosi.db'
    # یا به شکل زیر:
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{basedir}/instance/ferdosi.db"
   # اگر از os.path استفاده می‌کنید:
    #SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'ferdosi.db')}"


    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # تنظیمات فایل آپلود
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB محدودیت برای فایل‌های صوتی
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
    
    # تنظیمات Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # تنظیمات ایمیل - برای Gmail در محیط محلی
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # تنظیمات سایت
    SITE_NAME = 'فردوسی حسینی'
    SITE_URL = 'https://ferdowsihosseini.ir'
    INSTAGRAM_URL = 'https://instagram.com/Ferdowsi_Hosseini'
    TELEGRAM_URL = 'https://t.me/Ferdowsi_Hosseini'
    
    # تنظیمات جستجو
    SEARCH_RESULTS_PER_PAGE = 10
    
    @staticmethod
    def init_app(app):
        """اعمال تنظیمات روی اپلیکیشن"""
        # ایجاد پوشه آپلود در صورت عدم وجود
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه"""
    DEBUG = True

class ProductionConfig(Config):
    """تنظیمات محیط تولید"""
    DEBUG = False
    
    # تنظیمات SSL برای محیط تولید
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # تنظیمات لاگ برای محیط تولید
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('logs/ferdowsi_hosseini.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Ferdowsi Hosseini startup')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}