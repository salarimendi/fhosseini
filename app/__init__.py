#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
فایل اصلی اپلیکیشن فردوسی حسینی
"""

import os

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

from werkzeug.middleware.proxy_fix import ProxyFix

from config import config, env_config


# ============================================================
# Extensions
# ============================================================

db = SQLAlchemy()

login_manager = LoginManager()

mail = Mail()

csrf = CSRFProtect()

migrate = Migrate()

limiter = Limiter(
    key_func=get_remote_address
)

talisman = Talisman()


# ============================================================
# Application Factory
# ============================================================

def create_app(config_name=None):
    """ایجاد و تنظیم اپلیکیشن Flask."""

    # --------------------------------------------------------
    # تعیین محیط
    # --------------------------------------------------------

    if config_name is None:
        config_name = env_config(
            "FLASK_CONFIG",
            default="development"
        )

    if config_name not in config:
        raise ValueError(
            f"Unknown configuration: {config_name}"
        )

    config_class = config[config_name]

    # --------------------------------------------------------
    # ایجاد Flask
    # --------------------------------------------------------

    app = Flask(__name__)

    # --------------------------------------------------------
    # بارگذاری Configuration
    # --------------------------------------------------------

    app.config.from_object(config_class)

    config_class.init_app(app)

    # --------------------------------------------------------
    # Development settings
    # --------------------------------------------------------

    if app.config.get("DEBUG"):
        app.config["TEMPLATES_AUTO_RELOAD"] = True

        app.jinja_env.auto_reload = True

        app.jinja_env.cache = {}

        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # --------------------------------------------------------
    # ProxyFix
    # --------------------------------------------------------

    if app.config.get("SSL_ENABLED"):

        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=app.config["PROXY_FIX_X_FOR"],
            x_proto=app.config["PROXY_FIX_X_PROTO"],
            x_host=app.config["PROXY_FIX_X_HOST"],
            x_port=app.config["PROXY_FIX_X_PORT"],
            x_prefix=app.config["PROXY_FIX_X_PREFIX"]
        )

    # --------------------------------------------------------
    # Extensions initialization
    # --------------------------------------------------------

    db.init_app(app)

    login_manager.init_app(app)

    mail.init_app(app)

    csrf.init_app(app)

    migrate.init_app(app, db)

    limiter.init_app(app)

    # --------------------------------------------------------
    # Talisman
    # --------------------------------------------------------

    talisman.init_app(
        app,
        force_https=app.config["TALISMAN_FORCE_HTTPS"],
        strict_transport_security=(
            app.config["TALISMAN_STRICT_TRANSPORT_SECURITY"]
        ),
        strict_transport_security_max_age=(
            app.config[
                "TALISMAN_STRICT_TRANSPORT_SECURITY_MAX_AGE"
            ]
        ),
        strict_transport_security_include_subdomains=(
            app.config[
                "TALISMAN_STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS"
            ]
        ),
        session_cookie_secure=(
            app.config["SESSION_COOKIE_SECURE"]
        ),
        content_security_policy=(
            app.config["TALISMAN_CONTENT_SECURITY_POLICY"]
        )
    )

    # --------------------------------------------------------
    # Login Manager
    # --------------------------------------------------------

    login_manager.login_view = "auth.login"

    login_manager.login_message = (
        "لطفاً برای دسترسی به این صفحه وارد شوید."
    )

    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    # --------------------------------------------------------
    # Blueprints
    # --------------------------------------------------------

    from app.routes import register_blueprints

    register_blueprints(app)

    # --------------------------------------------------------
    # Database initialization
    # --------------------------------------------------------

    with app.app_context():

        db.create_all()
        from app.models import User

        admin_user = User.query.filter_by(
            username=app.config["ADMIN_USERNAME"]
        ).first()

        if not admin_user:

            admin_password = app.config["ADMIN_PASSWORD"]
            if not admin_password:
                raise RuntimeError(
                    "ADMIN_PASSWORD must be configured "
                    "when creating the initial admin user."
                )

            admin_user = User(
                username=app.config["ADMIN_USERNAME"],
                email=app.config["ADMIN_EMAIL"],
                fullname=app.config["ADMIN_FULLNAME"],
                role="admin"
            )

            admin_user.set_password(admin_password)

            db.session.add(admin_user)

            db.session.commit()

    # --------------------------------------------------------
    # Visit counter
    # --------------------------------------------------------

    from app.utils.visits import (
        increment_visit,
        get_visit_stats
    )

    @app.before_request
    def count_visit():

        if (
            not request.endpoint
            or request.endpoint.startswith("static")
        ):
            return

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":
            return

        try:
            increment_visit()

        except Exception as e:
            app.logger.error(
                f"خطا در شمارش بازدید: {e}"
            )

    # --------------------------------------------------------
    # Visit statistics
    # --------------------------------------------------------

    @app.context_processor
    def inject_visit_stats():

        try:
            return get_visit_stats()

        except Exception as e:

            app.logger.error(
                f"خطا در دریافت آمار بازدید: {e}"
            )

            return {
                "today_visits": 0,
                "total_visits": 0
            }

    # --------------------------------------------------------
    # Global template configuration
    # --------------------------------------------------------

    @app.context_processor
    def inject_config():

        return {
            "SITE_NAME": app.config["SITE_NAME"],
            "INSTAGRAM_URL": app.config["INSTAGRAM_URL"],
            "TELEGRAM_URL": app.config["TELEGRAM_URL"]
        }

    # --------------------------------------------------------
    # Persian number filter
    # --------------------------------------------------------

    @app.template_filter("persian_number")
    def persian_number_filter(number):
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"

        result = str(number)

        for i, digit in enumerate(english_digits):

            result = result.replace(
                digit,
                persian_digits[i]
            )

        return result

    return app