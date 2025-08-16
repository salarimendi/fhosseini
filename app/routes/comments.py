from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Comment, Title, Verse, User, db
from datetime import datetime

comments_bp = Blueprint('comments', __name__)

@comments_bp.route('/add_comment/<int:title_id>', methods=['POST'])
@login_required
def add_comment(title_id):
    """افزودن نظر محقق"""
    if not current_user.can_comment():
        flash('شما مجاز به ثبت نظر نیستید', 'error')
        return redirect(request.referrer or url_for('main.home'))
    
    data = request.get_json() if request.is_json else request.form
    comment_text = data.get('comment')
    
    if not comment_text:
        if request.is_json:
            return jsonify({'success': False, 'message': 'متن نظر نمی‌تواند خالی باشد'})
        flash('متن نظر نمی‌تواند خالی باشد', 'error')
        return redirect(request.referrer)
    
    # بررسی وجود شعر
    title = Title.query.get_or_404(title_id)
    
    # بررسی اینکه آیا محقق قبلاً نظر داده یا نه
    existing_comment = Comment.query.filter_by(
        user_id=current_user.id,
        title_id=title_id
    ).first()
    
    if existing_comment:
        if request.is_json:
            return jsonify({'success': False, 'message': 'شما قبلاً نظر خود را ثبت کرده‌اید'})
        flash('شما قبلاً نظر خود را ثبت کرده‌اید', 'error')
        return redirect(request.referrer)
    
    # ایجاد نظر جدید - نظرات ادمین مستقیماً تأیید می‌شوند
    new_comment = Comment(
        user_id=current_user.id,
        title_id=title_id,
        comment=comment_text,
        status='approved' if current_user.is_admin() else 'pending'
    )
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'نظر شما با موفقیت ثبت شد' + ('' if current_user.is_admin() else ' و پس از تأیید نمایش داده خواهد شد')})
        flash('نظر شما با موفقیت ثبت شد' + ('' if current_user.is_admin() else ' و پس از تأیید نمایش داده خواهد شد'), 'success')
        return redirect(request.referrer)
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': 'خطا در ثبت نظر'})
        flash('خطا در ثبت نظر', 'error')
        return redirect(request.referrer)

@comments_bp.route('/edit_comment/<int:comment_id>', methods=['POST'])
@login_required
def edit_comment(comment_id):
    """ویرایش نظر توسط مدیر یا صاحب نظر"""
    comment = Comment.query.get_or_404(comment_id)
    
    if not current_user.is_admin() and comment.user_id != current_user.id:
        flash('شما مجاز به ویرایش این نظر نیستید', 'error')
        return redirect(request.referrer)
    
    new_comment_text = request.form.get('comment')
    if not new_comment_text:
        flash('متن نظر نمی‌تواند خالی باشد', 'error')
        return redirect(request.referrer)
    
    try:
        comment.comment = new_comment_text
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('نظر با موفقیت ویرایش شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در ویرایش نظر', 'error')
    
    return redirect(request.referrer)

@comments_bp.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """حذف نظر توسط مدیر"""
    if not current_user.is_admin():
        flash('شما مجاز به حذف نظر نیستید', 'error')
        return redirect(request.referrer)
    
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('نظر با موفقیت حذف شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در حذف نظر', 'error')
    
    return redirect(request.referrer)

@comments_bp.route('/approve_comment/<int:comment_id>', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """تأیید نظر توسط مدیر"""
    if not current_user.is_admin():
        flash('شما مجاز به تأیید نظر نیستید', 'error')
        return redirect(request.referrer)
    
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        comment.is_approved = True
        db.session.commit()
        flash('نظر با موفقیت تأیید شد', 'success')
    except Exception as e:
        db.session.rollback()
        flash('خطا در تأیید نظر', 'error')
    
    return redirect(request.referrer)

@comments_bp.route('/get_comments/<int:title_id>')
def get_comments(title_id):
    """دریافت نظرات یک شعر"""
    comments = Comment.query.filter_by(title_id=title_id).join(User).all()
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'user': comment.author.username,
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%Y/%m/%d %H:%M'),
            'updated_at': comment.updated_at.strftime('%Y/%m/%d %H:%M') if comment.updated_at != comment.created_at else None,
            'is_approved': comment.is_approved,
            'can_edit': current_user.is_authenticated and (
                current_user.is_admin() or comment.user_id == current_user.id
            )
        })
    
    return jsonify({'comments': comments_data})