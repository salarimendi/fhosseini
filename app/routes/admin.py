from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import User, Comment, Recording, Title
from app import db, csrf
from functools import wraps
import os
import secrets
import json
from app.utils.database import save_research_form

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
    poems_count = Title.query.count()
    
    stats = {
        'users': users_count,
        'comments': comments_count,
        'recordings': recordings_count,
        'poems': poems_count
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

@admin_bp.route('/users/<int:user_id>/change-role', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_role(user_id):
    """تغییر نقش کاربر"""
    user = User.query.get_or_404(user_id)
    
    # جلوگیری از تغییر نقش خود
    if user.id == current_user.id:
        flash('نمی‌توانید نقش خود را تغییر دهید', 'error')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        new_role = request.form.get('new_role')
        
        if new_role not in ['user', 'researcher', 'reader', 'admin']:
            flash('نقش نامعتبر است', 'error')
            return redirect(url_for('admin.users'))
        
        try:
            user.role = new_role
            db.session.commit()
            flash('نقش کاربر با موفقیت تغییر کرد', 'success')
            return redirect(url_for('admin.users'))
        except:
            db.session.rollback()
            flash('خطا در تغییر نقش کاربر', 'error')
            return redirect(url_for('admin.users'))
    
    return render_template('admin/change_role.html', user=user)

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

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """بازنشانی رمز عبور کاربر"""
    user = User.query.get_or_404(user_id)
    
    try:
        # تولید رمز عبور تصادفی
        new_password = secrets.token_urlsafe(8)
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': f'رمز عبور جدید: {new_password}'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در بازنشانی رمز عبور'})

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """حذف کاربر"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'نمی‌توانید خودتان را حذف کنید'})
    
    try:
        # حذف فایل‌های صوتی قبل از حذف رکوردها
        recordings = Recording.query.filter_by(user_id=user.id).all()
        for recording in recordings:
            try:
                if os.path.exists(recording.file_path):
                    os.remove(recording.file_path)
            except:
                pass
        
        # حذف کاربر (با cascade، نظرات و رکوردها خودکار حذف می‌شوند)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'کاربر با موفقیت حذف شد'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در حذف کاربر'})

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

@admin_bp.route('/comments/delete/<int:comment_id>', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    """حذف نظر"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({
                'success': False, 
                'message': 'نظر مورد نظر یافت نشد'
            }), 404
        
        db.session.delete(comment)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'نظر با موفقیت حذف شد'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'خطا در حذف نظر: ' + str(e)
        }), 500

@admin_bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_comment(comment_id):
    """تأیید نظر"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        comment.status = 'approved'
        db.session.commit()
        return jsonify({'success': True, 'message': 'نظر با موفقیت تأیید شد'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در تأیید نظر'})

@admin_bp.route('/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_comment(comment_id):
    """رد نظر"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        comment.status = 'rejected'
        db.session.commit()
        return jsonify({'success': True, 'message': 'نظر با موفقیت رد شد'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در رد نظر'})

@admin_bp.route('/recordings')
@login_required
@admin_required
def recordings():
    """مدیریت ضبط‌های صوتی"""
    page = request.args.get('page', 1, type=int)
    
    # اعمال فیلترها
    query = Recording.query
    
    # فیلتر بر اساس جستجو
    search = request.args.get('search', '')
    if search:
        query = query.join(User).filter(User.username.ilike(f'%{search}%'))
    
    # فیلتر بر اساس باغ
    garden = request.args.get('garden')
    if garden:
        query = query.join(Title).filter(Title.garden == garden)
    
    # دریافت رکوردها با ترتیب نزولی تاریخ
    recordings = query.order_by(Recording.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # محاسبه آمار
    total_recordings = Recording.query.count()
    
    # محاسبه مجموع حجم فایل‌ها به صورت دستی
    all_recordings = Recording.query.all()
    total_size_mb = sum(rec.file_size_mb for rec in all_recordings if rec.file_size_mb is not None)
    
    active_readers = db.session.query(db.func.count(db.distinct(Recording.user_id))).scalar()
    recorded_poems = db.session.query(db.func.count(db.distinct(Recording.title_id))).scalar()

    stats = {
        'total_recordings': total_recordings,
        'total_size_mb': round(total_size_mb, 1),  # گرد کردن تا یک رقم اعشار
        'active_readers': active_readers,
        'recorded_poems': recorded_poems
    }

    return render_template('admin/recordings.html', recordings=recordings, stats=stats)

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
        return jsonify({'success': True, 'message': 'ضبط صوتی با موفقیت حذف شد'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در حذف ضبط صوتی'})

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """فعال/غیرفعال کردن کاربر"""
    user = User.query.get_or_404(user_id)
    
    # مدیر نمی‌تواند خودش را غیرفعال کند
    if user.id == current_user.id:
        flash('شما نمی‌توانید وضعیت خود را تغییر دهید.', 'error')
        return redirect(url_for('admin.users'))
    
    # تغییر وضعیت کاربر
    user.is_active = not user.is_active
    status = 'فعال' if user.is_active else 'غیرفعال'
    
    try:
        db.session.commit()
        flash(f'کاربر {user.username} با موفقیت {status} شد.', 'success')
    except:
        db.session.rollback()
        flash('خطا در تغییر وضعیت کاربر.', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/recordings/<int:recording_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_recording(recording_id):
    """تأیید ضبط صوتی"""
    recording = Recording.query.get_or_404(recording_id)
    
    try:
        recording.is_approved = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'ضبط صوتی با موفقیت تأیید شد'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در تأیید ضبط صوتی'})

@admin_bp.route('/recordings/<int:recording_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_recording(recording_id):
    """رد ضبط صوتی"""
    recording = Recording.query.get_or_404(recording_id)
    
    try:
        recording.is_approved = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'ضبط صوتی با موفقیت رد شد'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'خطا در رد ضبط صوتی'})

@admin_bp.route('/comments/<int:comment_id>/research-edit')
@login_required
@admin_required
def edit_comment_research(comment_id):
    """ویرایش نظر با فرم پژوهشی"""
    comment = Comment.query.get_or_404(comment_id)
    title = Title.query.get(comment.title_id) if comment.title_id else None
    
    try:
        comment_data = json.loads(comment.comment) if comment.comment else None
    except:
        comment_data = None
    
    return render_template('research/admin_form.html', 
                         title_id=comment.title_id,
                         poem_title=title.title if title else 'نظر عمومی',
                         comment_data=comment_data,
                         view_mode=False,
                         is_admin=True,
                         username=comment.author.username if comment.author else '',
                         comment=comment,
                         return_url=url_for('admin.comments'))

@admin_bp.route('/comments/<int:comment_id>/research-update', methods=['POST'])
@login_required
@admin_required
def update_comment_research(comment_id):
    """به‌روزرسانی نظر از فرم پژوهشی توسط ادمین (بدون تغییر user_id)"""
    comment = Comment.query.get_or_404(comment_id)
    try:
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict(flat=False)
            for k, v in data.items():
                if isinstance(v, list) and len(v) == 1:
                    data[k] = v[0]
            subtopics = json.loads(data.get('subtopics', '[]'))
            data['subtopics'] = subtopics
            files = request.files
            # حذف حلقه getlist کپشن
        else:
            if not request.is_json:
                flash('درخواست باید به صورت JSON یا فرم باشد', 'error')
                return redirect(url_for('admin.comments'))
            data = request.get_json()
            files = None
        # user_id و title_id را از comment اصلی می‌گیریم تا تغییر نکند
        data['user_id'] = comment.user_id
        data['title_id'] = comment.title_id
        comment_obj, message = save_research_form(comment, data, files, current_app.config, is_admin=True)
        flash(message, 'success')
    except ValueError as ve:
        flash(str(ve), 'error')
    except Exception as e:
        current_app.logger.error(f"Error saving research form (admin): {e}")
        flash('خطا در ثبت فرم پژوهشی', 'error')
    return redirect(url_for('admin.comments'))