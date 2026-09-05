#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
تنظیمات پروژه فردوسی حسینی

تمام مقادیر قابل تغییر محیطی از .env / Environment Variables
توسط python-decouple خوانده می‌شوند.

انتخاب محیط:
    FLASK_CONFIG=development
    FLASK_CONFIG=production
    FLASK_CONFIG=testing
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config as env_config


# ============================================================
# مسیر اصلی پروژه
# ============================================================

basedir = Path(__file__).resolve().parent


# ============================================================
# توابع کمکی
# ============================================================

def env_path(value: str, default: str) -> str:
    """
    مسیر را نسبت به ریشه پروژه تبدیل به مسیر مطلق می‌کند.

    اگر مسیر از قبل مطلق باشد، همان مسیر برگردانده می‌شود.
    """

    path = Path(value if value else default)

    if not path.is_absolute():
        path = basedir / path

    return str(path)


def get_bool(name: str, default: bool) -> bool:
    """خواندن مقدار boolean از environment."""

    return env_config(name, cast=bool, default=default)


# ============================================================
# Configuration پایه
# ============================================================

class Config:
    """تنظیمات مشترک تمام محیط‌ها."""

    # --------------------------------------------------------
    # Security
    # --------------------------------------------------------

    SECRET_KEY = env_config(
        "SECRET_KEY",
        default="dev-key-change-me"
    )

    WTF_CSRF_SECRET_KEY = env_config(
        "WTF_CSRF_SECRET_KEY",
        default="csrf-secret-change-me"
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    SQLALCHEMY_DATABASE_URI = env_config(
        "DATABASE_URL",
        default=f"sqlite:///{basedir / 'instance' / 'ferdosi.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    UPLOAD_MAX_SIZE_MB = env_config(
        "UPLOAD_MAX_SIZE_MB",
        cast=int,
        default=11
    )

    UPLOAD_FOLDER = env_path(
        env_config("UPLOAD_FOLDER", default="uploads"),
        "uploads"
    )

    MAX_CONTENT_LENGTH = UPLOAD_MAX_SIZE_MB * 1024 * 1024

    ALLOWED_EXTENSIONS = {
        "mp3",
        "wav",
        "ogg",
        "m4a"
    }

    # --------------------------------------------------------
    # Research images
    # --------------------------------------------------------

    RESEARCH_IMAGE_UPLOAD_FOLDER = env_path(
        env_config(
            "RESEARCH_IMAGE_UPLOAD_FOLDER",
            default="uploads/research_images"
        ),
        "uploads/research_images"
    )

    RESEARCH_IMAGE_MAX_SIZE_MB = env_config(
        "RESEARCH_IMAGE_MAX_SIZE_MB",
        cast=int,
        default=5
    )

    RESEARCH_IMAGE_ALLOWED_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp"
    }

    # --------------------------------------------------------
    # Articles images
    # --------------------------------------------------------

    ARTICLE_IMAGE_UPLOAD_FOLDER = env_config(
        'ARTICLE_IMAGE_UPLOAD_FOLDER',
        default=os.path.join(basedir, 'uploads', 'articles_images'),
    )
    ARTICLE_IMAGE_MAX_SIZE_MB = env_config('ARTICLE_IMAGE_MAX_SIZE_MB', cast=int, default=5)
    ARTICLE_IMAGE_ALLOWED_EXTENSIONS = set(
        e.strip() for e in env_config(
            'ARTICLE_IMAGE_ALLOWED_EXTENSIONS', default='jpg,jpeg,png,gif,webp'
        ).split(',') if e.strip()
    )
    ARTICLES_PER_PAGE = env_config('ARTICLES_PER_PAGE', cast=int, default=10)

    # --------------------------------------------------------
    # Session
    # --------------------------------------------------------

    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    # --------------------------------------------------------
    # Mail
    # --------------------------------------------------------

    MAIL_SERVER = env_config(
        "MAIL_SERVER",
        default="smtp.gmail.com"
    )

    MAIL_PORT = env_config(
        "MAIL_PORT",
        cast=int,
        default=587
    )

    MAIL_USE_TLS = get_bool(
        "MAIL_USE_TLS",
        True
    )

    MAIL_USERNAME = env_config(
        "MAIL_USERNAME",
        default=""
    )

    MAIL_PASSWORD = env_config(
        "MAIL_PASSWORD",
        default=""
    )

    MAIL_DEFAULT_SENDER = env_config(
        "MAIL_DEFAULT_SENDER",
        default=""
    )

    # --------------------------------------------------------
    # Website
    # --------------------------------------------------------

    SITE_NAME = env_config(
        "SITE_NAME",
        default="فردوسی حسینی"
    )

    SITE_URL = env_config(
        "SITE_URL",
        default="https://ferdowsihosseini.ir"
    )

    INSTAGRAM_URL = env_config(
        "INSTAGRAM_URL",
        default="https://instagram.com/ferdowsihosseini"
    )

    TELEGRAM_URL = env_config(
        "TELEGRAM_URL",
        default="https://t.me/ferdowsihosseini"
    )

    # --------------------------------------------------------
    # Rate Limiting
    # --------------------------------------------------------

    RATELIMIT_ENABLED = get_bool(
        "RATELIMIT_ENABLED",
        True
    )

    RATELIMIT_STORAGE_URL = env_config(
        "RATELIMIT_STORAGE_URL",
        default="memory://"
    )

    RATELIMIT_DEFAULT = env_config(
        "RATELIMIT_DEFAULT",
        default="200 per day;50 per hour;10 per minute"
    )

    RATELIMIT_LOGIN = env_config(
        "RATELIMIT_LOGIN",
        default="5 per minute"
    )

    RATELIMIT_HEADERS_ENABLED = get_bool(
        "RATELIMIT_HEADERS_ENABLED",
        True
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    SEARCH_RESULTS_PER_PAGE = env_config(
        "SEARCH_RESULTS_PER_PAGE",
        cast=int,
        default=10
    )

    # --------------------------------------------------------
    # SSL / HTTPS
    # --------------------------------------------------------

    SSL_ENABLED = get_bool(
        "SSL_ENABLED",
        False
    )

    PREFERRED_URL_SCHEME = "http"

    # --------------------------------------------------------
    # ProxyFix
    # --------------------------------------------------------

    PROXY_FIX_X_FOR = env_config(
        "PROXY_FIX_X_FOR",
        cast=int,
        default=1
    )

    PROXY_FIX_X_PROTO = env_config(
        "PROXY_FIX_X_PROTO",
        cast=int,
        default=1
    )

    PROXY_FIX_X_HOST = env_config(
        "PROXY_FIX_X_HOST",
        cast=int,
        default=1
    )

    PROXY_FIX_X_PORT = env_config(
        "PROXY_FIX_X_PORT",
        cast=int,
        default=1
    )

    PROXY_FIX_X_PREFIX = env_config(
        "PROXY_FIX_X_PREFIX",
        cast=int,
        default=1
    )

    # --------------------------------------------------------
    # Talisman / Security Headers
    # --------------------------------------------------------

    TALISMAN_FORCE_HTTPS = False

    TALISMAN_STRICT_TRANSPORT_SECURITY = False

    TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000

    TALISMAN_STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS = False

    TALISMAN_CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "img-src": [
            "'self'",
            "data:",
            "https:"
        ],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net"
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com"
        ],
        "font-src": [
            "'self'",
            "https://cdnjs.cloudflare.com"
        ],
        "frame-src": [
            "'self'",
            "https://www.aparat.com"
        ]
    }

    # --------------------------------------------------------
    # Admin initial account
    # --------------------------------------------------------

    ADMIN_USERNAME = env_config(
        "ADMIN_USERNAME",
        default="admin"
    )

    ADMIN_EMAIL = env_config(
        "ADMIN_EMAIL",
        default="admin@example.com"
    )

    ADMIN_FULLNAME = env_config(
        "ADMIN_FULLNAME",
        default="مدیر سایت"
    )

    ADMIN_PASSWORD = env_config(
        "ADMIN_PASSWORD",
        default=""
    )

    # --------------------------------------------------------
    # Init app
    # --------------------------------------------------------

    @staticmethod
    def init_app(app):
        """اعمال تنظیمات عمومی روی Flask."""

        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        os.makedirs(
            app.config["RESEARCH_IMAGE_UPLOAD_FOLDER"],
            exist_ok=True
        )

        os.makedirs(
            app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'], 
            exist_ok=True
        )

        os.makedirs(
            app.config["LOG_FOLDER"],
            exist_ok=True
        )

        os.makedirs(
            app.instance_path,
            exist_ok=True
        )

    @classmethod
    def get_upload_max_size_formatted(cls):
        """حجم مجاز فایل را به شکل 11M برمی‌گرداند."""

        return f"{cls.UPLOAD_MAX_SIZE_MB}M"


# ============================================================
# Development
# ============================================================

class DevelopmentConfig(Config):
    """تنظیمات محیط توسعه."""

    DEBUG = True

    TEMPLATES_AUTO_RELOAD = True

    PREFERRED_URL_SCHEME = "http"

    SSL_ENABLED = False

    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    RATELIMIT_STORAGE_URL = "memory://"

    RATELIMIT_DEFAULT = env_config(
        "RATELIMIT_DEFAULT",
        default="5000 per day;1000 per hour;200 per minute"
    )

    RATELIMIT_LOGIN = env_config(
        "RATELIMIT_LOGIN",
        default="100 per minute"
    )

    LOG_FOLDER = env_path(
        env_config("LOG_FOLDER", default="logs"),
        "logs"
    )


# ============================================================
# Production
# ============================================================

class ProductionConfig(Config):
    """تنظیمات محیط تولید."""

    DEBUG = False

    PREFERRED_URL_SCHEME = "https"

    SSL_ENABLED = True

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    RATELIMIT_DEFAULT = env_config(
        "RATELIMIT_DEFAULT",
        default="500 per day;100 per hour;20 per minute"
    )

    RATELIMIT_LOGIN = env_config(
        "RATELIMIT_LOGIN",
        default="10 per minute"
    )

    LOG_FOLDER = env_path(
        env_config("LOG_FOLDER", default="logs"),
        "logs"
    )

    TALISMAN_FORCE_HTTPS = True

    TALISMAN_STRICT_TRANSPORT_SECURITY = True

    TALISMAN_STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS = True

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import RotatingFileHandler

        log_file = os.path.join(
            cls.LOG_FOLDER,
            "ferdowsi_hosseini.log"
        )

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10240,
            backupCount=10
        )

        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s "
                "[in %(pathname)s:%(lineno)d]"
            )
        )

        file_handler.setLevel(logging.INFO)

        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)

        app.logger.info(
            "Ferdowsi Hosseini startup"
        )


# ============================================================
# Testing
# ============================================================

class TestingConfig(Config):
    """تنظیمات محیط تست."""

    TESTING = True

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    WTF_CSRF_ENABLED = False

    SERVER_NAME = "localhost:5000"

    PREFERRED_URL_SCHEME = "http"

    SSL_ENABLED = False

    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    RATELIMIT_STORAGE_URL = "memory://"

    RATELIMIT_DEFAULT = "10000 per day;1000 per hour;100 per minute"

    RATELIMIT_LOGIN = "5 per minute"

    LOG_FOLDER = env_path(
        env_config("LOG_FOLDER", default="logs"),
        "logs"
    )


# ============================================================
# Configuration map
# ============================================================

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}