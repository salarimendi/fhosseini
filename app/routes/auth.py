#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای احراز هویت پروژه فردوسی حسینی
"""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash
from app import db, mail, limiter
from app.models import User
from app.forms import LoginForm, ChangePasswordForm, RegisterForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # محدودیت 5 درخواست در دقیقه
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
    
    form = RegisterForm()
    if form.validate_on_submit():
        # بررسی تکراری نبودن نام کاربری و ایمیل
        if User.query.filter_by(username=form.username.data).first():
            flash('نام کاربری قبلاً استفاده شده است. ❌', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('ایمیل قبلاً ثبت شده است. ❌', 'error')
            return render_template('auth/register.html', form=form)
        
        # ایجاد کاربر جدید
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            fullname=form.fullname.data,  # این خط را اضافه کنید
            role=form.role.data,
            is_active=False  # کاربر جدید به صورت پیش‌فرض غیرفعال است
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('ثبت نام با موفقیت انجام شد. حساب کاربری شما پس از تایید مدیر فعال خواهد شد. 🎉', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash('خطا در ثبت نام. لطفاً دوباره تلاش کنید. ❌', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """خروج کاربر"""
    logout_user()
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/profile')
@login_required
def profile():
    """پروفایل کاربر"""
    return render_template('auth/profile.html')

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """تغییر رمز عبور"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('رمز عبور با موفقیت تغییر کرد.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('رمز عبور فعلی اشتباه است.', 'error')
    return render_template('auth/change_password.html', form=form)

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
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not password or len(password) < 6:
            flash('رمز عبور باید حداقل ۶ کاراکتر باشد.', 'error')
        elif password != password_confirm:
            flash('رمز عبور و تکرار آن باید یکسان باشند.', 'error')
        else:
            user.set_password(password)
            db.session.commit()
            session.pop(f'reset_token_{token}', None)
            flash('رمز عبور با موفقیت تغییر کرد. اکنون می‌توانید وارد شوید.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')

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
    reset_link = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message(
        'بازیابی رمز عبور - سایت فردوسی حسینی',
        sender=('فردوسی حسینی', 'noreply@ferdowsihosseini.ir'),
        recipients=[user.email]
    )
    
    msg.body = f'''برای بازیابی رمز عبور خود، روی لینک زیر کلیک کنید:

{reset_link}

اگر شما درخواست بازیابی رمز عبور نداده‌اید، این ایمیل را نادیده بگیرید.

با احترام،
تیم فردوسی حسینی
'''
    
    msg.html = f'''
<p>برای بازیابی رمز عبور خود، روی دکمه زیر کلیک کنید:</p>

<p><a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">بازیابی رمز عبور</a></p>

<p>یا می‌توانید لینک زیر را در مرورگر خود کپی کنید:</p>
<p><small>{reset_link}</small></p>

<p>اگر شما درخواست بازیابی رمز عبور نداده‌اید، این ایمیل را نادیده بگیرید.</p>

<p>با احترام،<br>
تیم فردوسی حسینی</p>
'''
    
    mail.send(msg)