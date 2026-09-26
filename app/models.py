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


# =========================
# کاربران
# =========================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_active = db.Column(db.Boolean, default=False)
    
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    recordings = db.relationship('Recording', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    def can_comment(self):
        return self.role in ['researcher', 'admin']

    def can_record(self):
        return self.role in ['reader', 'admin']

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


# =========================
# بازدید
# =========================

class Visit(db.Model):
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), unique=True, nullable=False)
    count = db.Column(db.Integer, default=0)


# =========================
# عناوین
# =========================

class Title(db.Model):
    __tablename__ = 'titles'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    garden = db.Column(db.Integer, nullable=False)
    order_in_garden = db.Column(db.Integer, nullable=False)
    
    verses = db.relationship('Verse', backref='title', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='poem_title', lazy='dynamic')
    recordings = db.relationship('Recording', backref='title', lazy='dynamic')

    @property
    def garden_name(self):
        garden_names = {
            1: 'خیابان اول باغ فردوس',
            2: 'خیابان دوم باغ فردوس', 
            3: 'خیابان سوم باغ فردوس',
            4: 'خیابان چهارم باغ فردوس'
        }
        return garden_names.get(self.garden, f'باغ {self.garden}')

    @property
    def verses_count(self):
        return self.verses.count()

    @property
    def approved_comments_count(self):
        return self.comments.filter_by(status='approved').count()

    @property
    def approved_recordings_count(self):
        return self.recordings.filter_by(is_approved=True).count()

    def get_verses_ordered(self):
        return self.verses.order_by(Verse.order_in_title).all()

    def get_comments(self):
        return self.comments.order_by(Comment.created_at.desc()).all()

    def preceding_verses_count(self):
        return db.session.query(Verse).join(Title).filter(
            Verse.is_subtitle == 0,
            (
                (Title.garden < self.garden) |
                ((Title.garden == self.garden) & (Title.order_in_garden < self.order_in_garden))
            )
        ).count()

    def __repr__(self):
        return f'<Title {self.title}>'


# =========================
# نسخ خطی
# =========================

class Version(db.Model):
    __tablename__ = 'versions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Version {self.name}>'


# =========================
# ابیات
# =========================

class Verse(db.Model):
    __tablename__ = 'verses'
    
    id = db.Column(db.Integer, primary_key=True)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'), nullable=False)
    order_in_title = db.Column(db.Integer, nullable=False)

    verse_1 = db.Column(db.Text, nullable=False)
    verse_2 = db.Column(db.Text)

    verse_1_tag = db.Column(db.Text, nullable=False)
    verse_2_tag = db.Column(db.Text)

    variant_diff = db.Column(db.Text)
    present_in_versions = db.Column(db.Text)

    is_subtitle = db.Column(db.Integer, nullable=False, default=0)

    # 👇 رابطه با جدول تصحیحات
    corrections = db.relationship(
        'VerseCorrection',
        backref='verse',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def full_verse(self):
        if self.verse_2:
            return f"{self.verse_1} *** {self.verse_2}"
        return self.verse_1

    def __repr__(self):
        return f'<Verse {self.id}: {self.verse_1[:40]}>'


# =========================
# جدول تصحیحات ابیات (جدید)
# =========================

class VerseCorrection(db.Model):
    __tablename__ = 'verse_corrections'

    id = db.Column(db.Integer, primary_key=True)

    verse_id = db.Column(
        db.Integer,
        db.ForeignKey('verses.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    field_name = db.Column(db.String(20), nullable=False)
    old_text = db.Column(db.Text)
    new_text = db.Column(db.Text, nullable=False)

    # نوع تصحیح
    # text | variant | vocalization | punctuation | other
    correction_type = db.Column(db.String(30), default='text')

    note = db.Column(db.Text)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)

    # روابط به کاربر ایجادکننده و تاییدکننده
    author = db.relationship('User', foreign_keys=[created_by], backref=db.backref('verse_corrections', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approved_by])

    def __repr__(self):
        return f'<VerseCorrection v={self.verse_id} field={self.field_name}>'


# =========================
# نظرات
# =========================

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'))

    comment = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))

    status = db.Column(db.String(20), default='pending')

    @property
    def author_name(self):
        return self.author.username if self.author else 'ناشناس'

    @property
    def is_approved(self):
        return self.status == 'approved'

    def __repr__(self):
        return f'<Comment by {self.author_name}>'


# =========================
# ضبط‌ها
# =========================

class Recording(db.Model):
    __tablename__ = 'recordings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'), nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))

    file_size = db.Column(db.Integer)
    duration = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_approved = db.Column(db.Boolean, default=False)

    @property
    def file_path(self):
        from flask import current_app
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.filename)

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    def __repr__(self):
        return f'<Recording {self.filename}>'


# =========================
# تصاویر پژوهشی
# =========================

class ResearchImage(db.Model):
    __tablename__ = 'research_images'

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    subtopic_index = db.Column(db.Integer, nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    caption = db.Column(db.String(500))
    file_size = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    comment = db.relationship(
        'Comment',
        backref=db.backref('research_images', lazy='dynamic', cascade='all, delete-orphan')
    )

    def __repr__(self):
        return f'<ResearchImage {self.filename}>'


# =========================
# کلاس کمکی جستجو
# =========================

class SearchResult:
    def __init__(self, title, content, url, type_name):
        self.title = title
        self.content = content
        self.url = url
        self.type_name = type_name

    def __repr__(self):
        return f'<SearchResult {self.title[:30]}>'
