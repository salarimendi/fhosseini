#!/usr/bin/env python3
"""
ابزار مدیریت مایگریشن‌های پایگاه داده
"""
import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade, init, migrate, downgrade
from app import create_app
from app.models import db

def create_migration_app():
    """ایجاد اپلیکیشن Flask برای مایگریشن"""
    app = create_app()
    return app

def init_db():
    """راه‌اندازی اولیه پایگاه داده و مایگریشن‌ها"""
    app = create_migration_app()
    
    with app.app_context():
        # بررسی وجود پوشه migrations
        if not os.path.exists('migrations'):
            print("راه‌اندازی اولیه مایگریشن‌ها...")
            init()
            print("✅ مایگریشن‌ها راه‌اندازی شدند")
        
        # ایجاد جداول
        print("ایجاد جداول پایگاه داده...")
        db.create_all()
        
        # اعمال مایگریشن‌ها
        print("اعمال مایگریشن‌ها...")
        try:
            upgrade()
            print("✅ مایگریشن‌ها با موفقیت اعمال شدند")
        except Exception as e:
            print(f"⚠️  خطا در اعمال مایگریشن‌ها: {e}")

def create_migration(message="Auto migration"):
    """ایجاد مایگریشن جدید"""
    app = create_migration_app()
    
    with app.app_context():
        try:
            migrate(message=message)
            print(f"✅ مایگریشن جدید ایجاد شد: {message}")
        except Exception as e:
            print(f"❌ خطا در ایجاد مایگریشن: {e}")

def upgrade_db():
    """بروزرسانی پایگاه داده"""
    app = create_migration_app()
    
    with app.app_context():
        try:
            upgrade()
            print("✅ پایگاه داده بروزرسانی شد")
        except Exception as e:
            print(f"❌ خطا در بروزرسانی: {e}")

def downgrade_db(revision='base'):
    """برگرداندن پایگاه داده به نسخه قبلی"""
    app = create_migration_app()
    
    with app.app_context():
        try:
            downgrade(revision=revision)
            print(f"✅ پایگاه داده به نسخه {revision} برگردانده شد")
        except Exception as e:
            print(f"❌ خطا در برگرداندن: {e}")

def reset_db():
    """بازنشانی کامل پایگاه داده"""
    app = create_migration_app()
    
    with app.app_context():
        try:
            # حذف همه جداول
            db.drop_all()
            print("🗑️  همه جداول حذف شدند")
            
            # ایجاد مجدد جداول
            db.create_all()
            print("✅ جداول مجدداً ایجاد شدند")
            
            # اعمال مایگریشن‌ها
            upgrade()
            print("✅ مایگریشن‌ها اعمال شدند")
            
        except Exception as e:
            print(f"❌ خطا در بازنشانی: {e}")

def show_help():
    """نمایش راهنما"""
    help_text = """