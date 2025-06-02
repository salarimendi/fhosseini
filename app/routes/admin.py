from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, Comment, Recording
from app import db
from functools import wraps
import os

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """دکوراتور برای محدود کردن دسترسی به مدیران"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('دسترسی غیرمجاز', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """داشبورد مدیریت"""
    users_count = User.query.count()
    comments_count = Comment.query.count()
    recordings_count = Recording.query.count()
    
    stats = {
        'users': users_count,
        'comments': comments_count,
        'recordings': recordings_count
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """مدیریت کاربران"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """ویرایش کاربر"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        
        # تغییر رمز عبور (اختیاری)
        new_password = request.form.get('password')
        if new_password:
            user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('کاربر با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash('خطا در به‌روزرسانی کاربر', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """حذف کاربر"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('نمی‌توانید خودتان را حذف کنید', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        # حذف فایل‌های صوتی قبل از حذف رکوردها
        recordings = Recording.query.filter_by(user_id=user.id).all()
        for recording in recordings:
            try:
                # استفاده از property file_path از مدل Recording
                if os.path.exists(recording.file_path):
                    os.remove(recording.file_path)
            except:
                pass
        
        # حذف کاربر (با cascade، نظرات و رکوردها خودکار حذف می‌شوند)
        db.session.delete(user)
        db.session.commit()
        
        flash('کاربر با موفقیت حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در حذف کاربر', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/comments')
@login_required
@admin_required
def comments():
    """مدیریت نظرات"""
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/comments.html', comments=comments)

@admin_bp.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_comment(comment_id):
    """ویرایش نظر"""
    comment = Comment.query.get_or_404(comment_id)
    
    if request.method == 'POST':
        comment.comment = request.form.get('comment')
        
        try:
            db.session.commit()
            flash('نظر با موفقیت به‌روزرسانی شد', 'success')
            return redirect(url_for('admin.comments'))
        except:
            db.session.rollback()
            flash('خطا در به‌روزرسانی نظر', 'error')
    
    return render_template('admin/edit_comment.html', comment=comment)

@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    """حذف نظر"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('نظر با موفقیت حذف شد', 'success')
    except:
        db.session.rollback()
        flash('خطا در حذف نظر', 'error')
    
    return redirect(url_for('admin.comments'))

@admin_bp.route('/recordings')
@login_required
@admin_required
def recordings():
    """مدیریت ضبط‌های صوتی"""
    page = request.args.get('page', 1, type=int)
    recordings = Recording.query.order_by(Recording.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/recordings.html', recordings=recordings)

@admin_bp.route('/recordings/<int:recording_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_recording(recording_id):
    """حذف ضبط صوتی"""
    recording = Recording.query.get_or_404(recording_id)
    
    try:
        # حذف فایل صوتی با استفاده از property file_path
        try:
            if os.path.exists(recording.file_path):
                os.remove(recording.file_path)
        except:
            pass
        
        db.session.delete(recording)
        db.session.commit()
        flash('ضبط صوتی با موفقیت حذف شد', 'success')
    except:
        db.session.rollback()
        flash('خطا در حذف ضبط صوتی', 'error')
    
    return redirect(url_for('admin.recordings'))@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """بازنشانی رمز عبور کاربر"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password:
        return jsonify({'success': False, 'message': 'رمز عبور جدید الزامی است'})
    
    try:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'رمز عبور با موفقیت تغییر یافت'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در تغییر رمز عبور'})

