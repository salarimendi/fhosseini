#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای احراز هویت پروژه فردوسی حسینی
"""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from app import db, mail
from app.models import User
from app.forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ورود کاربر"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        remember = form.remember_me.data
        
        # جستجوی کاربر بر اساس نام کاربری یا ایمیل
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            
            # هدایت به صفحه مورد نظر یا صفحه اصلی
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            flash(f'خوش آمدید، {user.username}!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """ثبت نام کاربر جدید"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        role = request.form.get('role', 'user')
        
        # اعتبارسنجی
        errors = []
        
        if not username or len(username) < 3:
            errors.append('نام کاربری باید حداقل ۳ کاراکتر باشد.')
        
        if not email or '@' not in email:
            errors.append('ایمیل معتبر وارد کنید.')
        
        if not password or len(password) < 6:
            errors.append('رمز عبور باید حداقل ۶ کاراکتر باشد.')
        
        if password != password_confirm:
            errors.append('تکرار رمز عبور مطابقت ندارد.')
        
        # بررسی نقش‌های مجاز (بر اساس models.py)
        if role not in ['user', 'researcher', 'reader']:
            role = 'user'
        
        # بررسی تکراری نبودن
        if User.query.filter_by(username=username).first():
            errors.append('نام کاربری قبلاً استفاده شده است.')
        
        if User.query.filter_by(email=email).first():
            errors.append('ایمیل قبلاً ثبت شده است.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # ایجاد کاربر جدید
        user = User(
            username=username,
            email=email,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            flash('ثبت نام با موفقیت انجام شد. می‌توانید وارد شوید.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash('خطا در ثبت نام. لطفاً دوباره تلاش کنید.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """خروج کاربر"""
    logout_user()
    flash('با موفقیت خارج شدید.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/profile')
@login_required
def profile():
    """پروفایل کاربر"""
    
    # آمار کاربر بر اساس روابط تعریف شده در models.py
    stats = {
        'comments_count': current_user.comments.count(),
        'recordings_count': current_user.recordings.count(),
        'approved_comments': current_user.comments.filter_by(is_approved=True).count(),
        'approved_recordings': current_user.recordings.filter_by(is_approved=True).count(),
    }
    
    return render_template('auth/profile.html', stats=stats)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغییر رمز عبور"""
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # اعتبارسنجی
        if not current_user.check_password(current_password):
            flash('رمز عبور فعلی اشتباه است.', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('رمز عبور جدید باید حداقل ۶ کاراکتر باشد.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('تکرار رمز عبور جدید مطابقت ندارد.', 'error')
            return render_template('auth/change_password.html')
        
        # تغییر رمز عبور
        current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('رمز عبور با موفقیت تغییر کرد.', 'success')
            return redirect(url_for('auth.profile'))
        
        except Exception as e:
            db.session.rollback()
            flash('خطا در تغییر رمز عبور.', 'error')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """فراموشی رمز عبور"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('لطفاً ایمیل خود را وارد کنید.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active:
            # ایجاد توکن بازیابی
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.utcnow() + timedelta(hours=2)
            
            # ذخیره در session (در محیط واقعی باید در دیتابیس ذخیره شود)
            session[f'reset_token_{reset_token}'] = {
                'user_id': user.id,
                'expires': reset_expires.isoformat()
            }
            
            # ارسال ایمیل
            try:
                send_reset_email(user, reset_token)
                flash('لینک بازیابی رمز عبور به ایمیل شما ارسال شد.', 'success')
            except Exception as e:
                flash('خطا در ارسال ایمیل. لطفاً دوباره تلاش کنید.', 'error')
        else:
            # برای امنیت، همیشه پیام موفقیت نمایش می‌دهیم
            flash('اگر ایمیل معتبر باشد، لینک بازیابی ارسال خواهد شد.', 'info')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """بازنشانی رمز عبور"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # بررسی معتبر بودن توکن
    reset_data = session.get(f'reset_token_{token}')
    if not reset_data:
        flash('لینک بازیابی معتبر نیست.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # بررسی انقضا
    expires = datetime.fromisoformat(reset_data['expires'])
    if datetime.utcnow() > expires:
        session.pop(f'reset_token_{token}', None)
        flash('لینک بازیابی منقضی شده است.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.get(reset_data['user_id'])
    if not user or not user.is_active:
        flash('کاربر یافت نشد.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(new_password) < 6:
            flash('رمز عبور باید حداقل ۶ کاراکتر باشد.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('تکرار رمز عبور مطابقت ندارد.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # تغییر رمز عبور
        user.set_password(new_password)
        
        try:
            db.session.commit()
            session.pop(f'reset_token_{token}', None)
            
            flash('رمز عبور با موفقیت تغییر کرد. می‌توانید وارد شوید.', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash('خطا در تغییر رمز عبور.', 'error')
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/users')
@login_required
def users_list():
    """لیست کاربران - فقط برای مدیران"""
    
    if not current_user.is_admin():
        flash('شما مجوز دسترسی به این صفحه را ندارید.', 'error')
        return redirect(url_for('main.home'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/users_list.html', users=users)

@auth_bp.route('/toggle_user_status/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    """فعال/غیرفعال کردن کاربر - فقط برای مدیران"""
    
    if not current_user.is_admin():
        flash('شما مجوز دسترسی به این عملیات را ندارید.', 'error')
        return redirect(url_for('main.home'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('نمی‌توانید وضعیت خود را تغییر دهید.', 'error')
        return redirect(url_for('auth.users_list'))
    
    user.is_active = not user.is_active
    
    try:
        db.session.commit()
        status = 'فعال' if user.is_active else 'غیرفعال'
        flash(f'وضعیت کاربر {user.username} به {status} تغییر کرد.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در تغییر وضعیت کاربر.', 'error')
    
    return redirect(url_for('auth.users_list'))

def send_reset_email(user, token):
    """ارسال ایمیل بازیابی رمز عبور"""
    
    msg = Message(
        subject='بازیابی رمز عبور - فردوسی حسینی',
        recipients=[user.email],
        html=render_template('emails/reset_password.html', 
                           user=user, 
                           token=token)
    )
    
    mail.send(msg)