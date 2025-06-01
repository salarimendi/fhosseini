#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای مربوط به ابیات و ضبط صدا - پروژه فردوسی حسینی
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Title, Verse, Recording

verses_bp = Blueprint('verses', __name__)

def allowed_file(filename):
    """بررسی مجاز بودن فرمت فایل صوتی"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_file_size(file_path):
    """دریافت اندازه فایل"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

@verses_bp.route('/record/<int:title_id>', methods=['GET', 'POST'])
@login_required
def record_audio(title_id):
    """ضبط صدا برای یک شعر"""
    
    # بررسی مجوز ضبط
    if not current_user.can_record():
        flash('شما مجوز ضبط صدا ندارید.', 'error')
        return redirect(url_for('main.title', title_id=title_id))
    
    title_obj = Title.query.get_or_404(title_id)
    
    # بررسی اینکه آیا کاربر قبلاً برای این شعر ضبط کرده یا نه
    existing_recording = Recording.query.filter_by(
        user_id=current_user.id,
        title_id=title_id
    ).first()
    
    if request.method == 'POST':
        # بررسی اینکه آیا فایل آپلود شده یا نه
        if 'audio_file' not in request.files:
            flash('فایل صوتی انتخاب نشده است.', 'error')
            return redirect(request.url)
        
        file = request.files['audio_file']
        
        if file.filename == '':
            flash('فایل صوتی انتخاب نشده است.', 'error')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('فرمت فایل مجاز نیست. فرمت‌های مجاز: mp3, wav, ogg, m4a', 'error')
            return redirect(request.url)
        
        # بررسی اندازه فایل
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            flash('اندازه فایل نباید بیشتر از ۵ مگابایت باشد.', 'error')
            return redirect(request.url)
        
        # ایجاد نام فایل یکتا
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # مسیر ذخیره فایل
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        
        try:
            # ذخیره فایل
            file.save(file_path)
            
            # ایجاد یا به‌روزرسانی رکورد ضبط
            if existing_recording:
                # حذف فایل قبلی
                old_file_path = os.path.join(upload_folder, existing_recording.filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                # به‌روزرسانی اطلاعات
                existing_recording.filename = unique_filename
                existing_recording.original_filename = secure_filename(file.filename)
                existing_recording.file_size = file_size
                existing_recording.created_at = datetime.utcnow()
                
                db.session.commit()
                flash('ضبط صوتی با موفقیت به‌روزرسانی شد.', 'success')
            
            else:
                # ایجاد رکورد جدید
                new_recording = Recording(
                    user_id=current_user.id,
                    title_id=title_id,
                    filename=unique_filename,
                    original_filename=secure_filename(file.filename),
                    file_size=file_size
                )
                
                db.session.add(new_recording)
                db.session.commit()
                flash('ضبط صوتی با موفقیت ذخیره شد.', 'success')
            
            return redirect(url_for('main.title', title_id=title_id))
        
        except Exception as e:
            db.session.rollback()
            # حذف فایل در صورت خطا
            if os.path.exists(file_path):
                os.remove(file_path)
            
            flash('خطا در ذخیره فایل صوتی.', 'error')
            current_app.logger.error(f"Error saving audio file: {e}")
    
    return render_template('verses/record_audio.html', 
                         title=title_obj, 
                         existing_recording=existing_recording)

@verses_bp.route('/play/<int:recording_id>')
def play_audio(recording_id):
    """پخش فایل صوتی"""
    
    recording = Recording.query.get_or_404(recording_id)
    
    if not recording.is_approved:
        flash('این ضبط صوتی هنوز تأیید نشده است.', 'error')
        return redirect(url_for('main.index'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recording.filename)
    
    if not os.path.exists(file_path):
        flash('فایل صوتی یافت نشد.', 'error')
        return redirect(url_for('main.title', title_id=recording.title_id))
    
    return send_file(file_path, as_attachment=False)

@verses_bp.route('/download/<int:recording_id>')
def download_audio(recording_id):
    """دانلود فایل صوتی"""
    
    recording = Recording.query.get_or_404(recording_id)
    
    if not recording.is_approved:
        flash('این ضبط صوتی هنوز تأیید نشده است.', 'error')
        return redirect(url_for('main.index'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recording.filename)
    
    if not os.path.exists(file_path):
        flash('فایل صوتی یافت نشد.', 'error')
        return redirect(url_for('main.title', title_id=recording.title_id))
    
    # نام فایل برای دانلود
    download_name = f"{recording.title.title}_{recording.user.username}.{recording.filename.split('.')[-1]}"
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=download_name)

@verses_bp.route('/delete_recording/<int:recording_id>', methods=['POST'])
@login_required
def delete_recording(recording_id):
    """حذف ضبط صوتی"""
    
    recording = Recording.query.get_or_404(recording_id)
    
    # بررسی مجوز حذف
    if not (current_user.id == recording.user_id or current_user.is_admin()):
        flash('شما مجوز حذف این ضبط را ندارید.', 'error')
        return redirect(url_for('main.title', title_id=recording.title_id))
    
    try:
        # حذف فایل از سیستم
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recording.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        title_id = recording.title_id
        
        # حذف رکورد از دیتابیس
        db.session.delete(recording)
        db.session.commit()
        
        flash('ضبط صوتی با موفقیت حذف شد.', 'success')
        return redirect(url_for('main.title', title_id=title_id))
    
    except Exception as e:
        db.session.rollback()
        flash('خطا در حذف ضبط صوتی.', 'error')
        current_app.logger.error(f"Error deleting recording: {e}")
        return redirect(url_for('main.title', title_id=recording.title_id))

@verses_bp.route('/my_recordings')
@login_required
def my_recordings():
    """نمایش ضبط‌های صوتی کاربر"""
    
    recordings = Recording.query.filter_by(user_id=current_user.id)\
                               .order_by(Recording.created_at.desc())\
                               .all()
    
    return render_template('verses/my_recordings.html', recordings=recordings)

@verses_bp.route('/api/recordings/<int:title_id>')
def api_recordings(title_id):
    """API برای دریافت ضبط‌های صوتی یک شعر"""
    
    title_obj = Title.query.get_or_404(title_id)
    
    recordings_data = []
    for recording in title_obj.recordings:
        if recording.is_approved:
            recordings_data.append({
                'id': recording.id,
                'reader_name': recording.user.username,
                'filename': recording.filename,
                'file_size_mb': recording.file_size_mb,
                'created_at': recording.created_at.strftime('%Y/%m/%d'),
                'play_url': url_for('verses.play_audio', recording_id=recording.id),
                'download_url': url_for('verses.download_audio', recording_id=recording.id)
            })
    
    return jsonify({
        'title': title_obj.title,
        'recordings': recordings_data,
        'count': len(recordings_data)
    })

@verses_bp.route('/compare_versions/<int:title_id>')
def compare_versions(title_id):
    """مقایسه نسخه‌های مختلف یک شعر"""
    
    title_obj = Title.query.get_or_404(title_id)
    
    # دریافت ابیات اصلی
    main_verses = title_obj.get_verses_ordered()
    
    # دریافت نسخه‌های مختلف (در صورت وجود)
    version_verses = title_obj.version_verses.all()
    
    return render_template('verses/compare_versions.html',
                         title=title_obj,
                         main_verses=main_verses,
                         version_verses=version_verses)