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
        return jsonify({'success': False, 'message': 'شما مجوز ضبط صدا ندارید.'})
    
    title_obj = Title.query.get_or_404(title_id)
    
    # بررسی اینکه آیا کاربر قبلاً برای این شعر ضبط کرده یا نه
    existing_recording = Recording.query.filter_by(
        user_id=current_user.id,
        title_id=title_id
    ).first()
    
    if request.method == 'POST':
        # بررسی اینکه آیا فایل آپلود شده یا نه
        if 'audio_file' not in request.files:
            return jsonify({'success': False, 'message': 'فایل صوتی انتخاب نشده است.'})
        
        file = request.files['audio_file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'فایل صوتی انتخاب نشده است.'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'فرمت فایل مجاز نیست. فرمت‌های مجاز: mp3, wav, ogg, m4a'})
        
        # بررسی اندازه فایل
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'message': 'اندازه فایل نباید بیشتر از ۵ مگابایت باشد.'})
        
        try:
            # ایجاد نام فایل یکتا
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"garden{title_obj.garden}_poem{title_id}_{current_user.username}_{timestamp}.{file_extension}"
            
            # مسیر ذخیره فایل
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            
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
                existing_recording.is_approved = False  # ریست کردن وضعیت تأیید
                
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'ضبط صوتی جدید با موفقیت جایگزین شد و در انتظار تأیید است.'
                })
            
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
                return jsonify({
                    'success': True,
                    'message': 'ضبط صوتی با موفقیت ذخیره شد.'
                })
            
        except Exception as e:
            db.session.rollback()
            # حذف فایل در صورت خطا
            if os.path.exists(file_path):
                os.remove(file_path)
            
            current_app.logger.error(f"Error saving audio file: {e}")
            return jsonify({
                'success': False,
                'message': 'خطا در ذخیره فایل صوتی.'
            })
    
    # برای درخواست GET، صفحه ضبط را نمایش می‌دهیم
    return render_template('verses/record_audio.html', 
                         title=title_obj, 
                         existing_recording=existing_recording)

@verses_bp.route('/play/<int:recording_id>')
def play_audio(recording_id):
    """پخش فایل صوتی"""
    
    recording = Recording.query.get_or_404(recording_id)
    
    # اجازه پخش برای ادمین‌ها و فایل‌های تأیید شده
    if not recording.is_approved and not (current_user.is_authenticated and current_user.is_admin()):
        flash('این ضبط صوتی هنوز تأیید نشده است.', 'error')
        return redirect(url_for('main.home'))
    
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
        return redirect(url_for('main.home'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], recording.filename)
    
    if not os.path.exists(file_path):
        flash('فایل صوتی یافت نشد.', 'error')
        return redirect(url_for('main.title', title_id=recording.title_id))
    
    # نام فایل برای دانلود - استفاده از relationship که در models تعریف شده
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
    # استفاده از relationship که در models تعریف شده
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
    
    # دریافت ابیات اصلی - استفاده از متد موجود در models
    main_verses = title_obj.get_verses_ordered()
    
    # حذف بخش version_verses چون در models تعریف نشده
    # فقط ابیات اصلی را نمایش می‌دهیم
    
    return render_template('verses/compare_versions.html',
                         title=title_obj,
                         main_verses=main_verses)