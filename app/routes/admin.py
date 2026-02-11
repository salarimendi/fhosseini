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
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.utils.database import (
    get_corrections_filtered,
    approve_verse_correction,
    reject_verse_correction,
    get_pending_corrections_count
)



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
    from app.models import VerseCorrection
    
    users_count = User.query.count()
    comments_count = Comment.query.count()
    recordings_count = Recording.query.count()
    poems_count = Title.query.count()
    pending_corrections_count = VerseCorrection.query.filter_by(is_approved=False).count()
    approved_corrections_count = VerseCorrection.query.filter_by(is_approved=True).count()
    
    # آخرین کاربران
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # آخرین نظرات
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    stats = {
        'users': users_count,
        'comments': comments_count,
        'recordings': recordings_count,
        'poems': poems_count,
        'pending_corrections': pending_corrections_count,
        'approved_corrections': approved_corrections_count
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_comments=recent_comments)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """مدیریت کاربران"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # شروع query
    query = User.query
    
    # اعمال فیلتر جستجو
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.fullname.ilike(f'%{search}%')
            )
        )
    
    # اعمال فیلتر نقش
    role_filter = request.args.get('role', '')
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    # مرتب‌سازی و صفحه‌بندی
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
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
    per_page = 20
    
    # شروع query با join به Title
    query = Comment.query.join(Title, Comment.title_id == Title.id, isouter=True)
    
    # اعمال فیلتر جستجو
    search = request.args.get('search', '')
    if search:
        query = query.join(User).filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                Comment.comment.ilike(f'%{search}%')
            )
        )
    
    # اعمال فیلتر محقق
    researcher_filter = request.args.get('researcher', '', type=str)
    if researcher_filter:
        try:
            researcher_id = int(researcher_filter)
            query = query.filter(Comment.user_id == researcher_id)
        except ValueError:
            pass
    
    # اعمال فیلتر وضعیت
    status_filter = request.args.get('status', '')
    if status_filter:
        query = query.filter(Comment.status == status_filter)
    
    # اعمال فیلتر باغ
    garden_filter = request.args.get('garden', '', type=str)
    if garden_filter:
        try:
            garden_num = int(garden_filter)
            query = query.filter(Title.garden == garden_num)
        except ValueError:
            pass
    
    # اعمال فیلتر ترتیب شعر در باغ
    order_filter = request.args.get('order', '', type=str)
    if order_filter:
        try:
            order_num = int(order_filter)
            query = query.filter(Title.order_in_garden == order_num)
        except ValueError:
            pass
    
    # مرتب‌سازی و صفحه‌بندی
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # دریافت لیست باغ‌ها برای dropdown
    gardens = db.session.query(
        Title.garden,
        db.func.count(db.distinct(Title.id)).label('count')
    ).group_by(Title.garden).order_by(Title.garden).all()
    
    # دریافت لیست محققین با تعداد نظرات - اصلاح شده
    researchers = db.session.query(
        User.id,
        User.username,
        db.func.count(Comment.id).label('comment_count')
    ).outerjoin(Comment, User.id == Comment.user_id)\
     .filter(User.role == 'researcher')\
     .group_by(User.id, User.username)\
     .order_by(User.username)\
     .all()
    
    return render_template('admin/comments.html', 
                         comments=comments, 
                         gardens=gardens,
                         researchers=researchers)




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
        'total_size_mb': round(total_size_mb, 1),
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
    """ویرایش نظر با فرم پژوهشی - بدون مدیریت عکس در این صفحه"""
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
    """به‌روزرسانی نظر از فرم پژوهشی توسط ادمین - فقط بخش متنی (بدون عکس)"""
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        # دریافت داده‌ها
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict(flat=False)
            # تبدیل مقادیر تک مقداری به مقدار ساده
            for k, v in data.items():
                if isinstance(v, list) and len(v) == 1:
                    data[k] = v[0]
            
            # تبدیل JSON subtopics
            subtopics = json.loads(data.get('subtopics', '[]'))
            data['subtopics'] = subtopics
        else:
            if not request.is_json:
                return jsonify({'success': False, 'message': 'درخواست باید به صورت JSON یا فرم باشد'}), 400
            data = request.get_json()
        
        # user_id و title_id را از comment اصلی می‌گیریم تا تغییر نکند
        data['user_id'] = comment.user_id
        data['title_id'] = comment.title_id
        
        # ذخیره فرم پژوهشی (فقط بخش متنی، بدون عکس)
        comment_obj, message = save_research_form(
            comment, 
            data, 
            None,  # files=None چون عکس‌ها جداگانه مدیریت می‌شوند
            current_app.config, 
            is_admin=True
        )
        
        return jsonify({
            'success': True, 
            'message': message, 
            'return_url': url_for('admin.comments')
        })
        
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error saving research form (admin): {e}")
        return jsonify({'success': False, 'message': 'خطا در ثبت فرم پژوهشی'}), 500
    

    
# =============================================================================
# صفحه مدیریت نظرات
# =============================================================================

@admin_bp.route('/admin/corrections')
@login_required
def admin_corrections():
    """
    صفحه مدیریت نظرات تصحیحی
    
    Query Parameters:
        - page: int (default: 1)
        - status: str ('' | 'approved' | 'pending')
        - search: str
    
    Returns:
        Template با لیست نظرات
    """
    # بررسی دسترسی ادمین
    if not current_user.is_admin():
        flash('دسترسی غیرمجاز', 'danger')
        return redirect(url_for('index'))
    
    # دریافت پارامترها
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # دریافت نظرات با فیلتر
    corrections = get_corrections_filtered(
        page=page,
        per_page=20,
        status=status,
        search=search
    )
    
    # تعداد نظرات در انتظار
    pending_count = get_pending_corrections_count()
    
    return render_template('admin/corrections.html',
                         corrections=corrections,
                         pending_count=pending_count,
                         status=status,
                         search=search)


# =============================================================================
# API Endpoints برای تایید/رد نظرات
# =============================================================================

@admin_bp.route('/admin/correction/<int:correction_id>/approve', methods=['POST'])
@login_required
def admin_approve_correction(correction_id):
    """
    تایید نظر تصحیحی
    
    Parameters:
        - correction_id: شناسه نظر
    
    Response:
        - success: bool
        - message: str
    """
    # بررسی دسترسی ادمین
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
    
    try:
        message = approve_verse_correction(correction_id, current_user.id)
        return jsonify({'success': True, 'message': message})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error approving correction {correction_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'خطا در تایید نظر'}), 500


@admin_bp.route('/admin/correction/<int:correction_id>/reject', methods=['POST'])
@login_required
def admin_reject_correction(correction_id):
    """
    رد نظر تصحیحی (حذف)
    
    Parameters:
        - correction_id: شناسه نظر
    
    Response:
        - success: bool
        - message: str
    """
    # بررسی دسترسی ادمین
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'دسترسی غیرمجاز'}), 403
    
    try:
        message = reject_verse_correction(correction_id)
        return jsonify({'success': True, 'message': message})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error rejecting correction {correction_id}: {str(e)}")
        return jsonify({'success': False, 'message': 'خطا در رد نظر'}), 500


# =============================================================================
# Context Processor برای نمایش تعداد نظرات pending در منو
# =============================================================================

@admin_bp.context_processor
def inject_pending_corrections_count():
    """
    اضافه کردن تعداد نظرات pending به context برای نمایش در منوی ادمین
    
    این تابع به صورت خودکار در تمام template ها اجرا می‌شود
    """
    if current_user.is_authenticated and current_user.is_admin():
        return {
            'pending_corrections_count': get_pending_corrections_count()
        }
    return {}


# =============================================================================
# پایان Route های مدیریت نظرات تصحیحی
# =============================================================================
