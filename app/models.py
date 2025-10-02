#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدل‌های پایگاه داده پروژه فردوسی حسینی
"""

from datetime import datetime, UTC
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import os

class User(UserMixin, db.Model):
    """مدل کاربران"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_active = db.Column(db.Boolean, default=False)
    
    # روابط
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    recordings = db.relationship('Recording', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """تنظیم رمز عبور"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """بررسی رمز عبور"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """بررسی نقش کاربر"""
        return self.role == role
    
    def can_comment(self):
        """آیا کاربر می‌تواند نظر بدهد؟"""
        return self.role in ['researcher', 'admin']
    
    def can_record(self):
        """آیا کاربر می‌تواند صدا ضبط کند؟"""
        return self.role in ['reader', 'admin']
    
    def is_admin(self):
        """آیا کاربر مدیر است؟"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Visit(db.Model):
    """مدل آمار بازدید روزانه"""
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), unique=True, nullable=False)  # YYYY-MM-DD
    count = db.Column(db.Integer, default=0)

class Title(db.Model):
    """مدل عناوین اشعار"""
    __tablename__ = 'titles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    garden = db.Column(db.Integer, nullable=False)  # شماره باغ (۱-۴)
    order_in_garden = db.Column(db.Integer, nullable=False)
    
    # روابط
    verses = db.relationship('Verse', backref='title', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='poem_title', lazy='dynamic')
    recordings = db.relationship('Recording', backref='title', lazy='dynamic')
    
    @property
    def garden_name(self):
        """نام باغ بر اساس شماره"""
        garden_names = {
            1: 'خیابان اول باغ فردوس',
            2: 'خیابان دوم باغ فردوس', 
            3: 'خیابان سوم باغ فردوس',
            4: 'خیابان چهارم باغ فردوس'
        }
        return garden_names.get(self.garden, f'باغ {self.garden}')
    
    @property
    def verses_count(self):
        """تعداد کل ابیات"""
        return self.verses.count()
    
    @property
    def approved_comments_count(self):
        """تعداد نظرات تایید شده"""
        return self.comments.filter_by(status='approved').count()
    
    @property
    def approved_recordings_count(self):
        """تعداد فایل‌های صوتی تایید شده"""
        return self.recordings.filter_by(is_approved=True).count()
    
    def get_verses_ordered(self):
        """دریافت ابیات مرتب شده"""
        return self.verses.order_by(Verse.order_in_title).all()
    
    def get_comments(self):
        """دریافت نظرات مربوط به این شعر"""
        return self.comments.order_by(Comment.created_at.desc()).all()
    
    def __repr__(self):
        return f'<Title {self.title}>'

class Verse(db.Model):
    """مدل ابیات"""
    __tablename__ = 'verses'
    
    id = db.Column(db.Integer, primary_key=True)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'), nullable=False)
    order_in_title = db.Column(db.Integer, nullable=False)
    verse_1 = db.Column(db.Text, nullable=False)  # مصراع اول
    verse_2 = db.Column(db.Text)  # مصراع دوم (اختیاری)
    
    @property
    def full_verse(self):
        """بیت کامل"""
        if self.verse_2:
            return f"{self.verse_1} *** {self.verse_2}"
        return self.verse_1
    
    def __repr__(self):
        return f'<Verse {self.id}: {self.verse_1[:50]}...>'

class Comment(db.Model):
    """مدل نظرات محققین"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'))
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # وضعیت: pending, approved, rejected
    
    @property
    def author_name(self):
        """نام نویسنده نظر"""
        return self.author.username if self.author else 'ناشناس'
    
    @property
    def is_approved(self):
        """برای حفظ سازگاری با کد قبلی"""
        return self.status == 'approved'
    
    def __repr__(self):
        return f'<Comment by {self.author_name}>'

class Recording(db.Model):
    """مدل ضبط‌های صوتی"""
    __tablename__ = 'recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)  # اندازه فایل به بایت
    duration = db.Column(db.Float)  # مدت زمان به ثانیه
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    
    @property
    def file_path(self):
        """مسیر کامل فایل"""
        from flask import current_app
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.filename)
    
    @property
    def file_size_mb(self):
        """اندازه فایل به مگابایت"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def __repr__(self):
        return f'<Recording {self.filename} by {self.user.username}>'

class ResearchImage(db.Model):
    __tablename__ = 'research_images'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    subtopic_index = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    caption = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comment = db.relationship('Comment', backref=db.backref('research_images', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ResearchImage {self.filename} for comment {self.comment_id}>'

# کلاس کمکی برای جستجو
class SearchResult:
    """کلاس نتایج جستجو"""
    
    def __init__(self, title, content, url, type_name):
        self.title = title
        self.content = content
        self.url = url
        self.type_name = type_name
    
    def __repr__(self):
        return f'<SearchResult {self.title[:30]}>'