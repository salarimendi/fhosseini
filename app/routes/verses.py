#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای مربوط به ابیات و ضبط صدا - پروژه فردوسی حسینی
"""

import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Title, Verse, Recording, Comment, User
from app.utils.database import save_research_form

verses_bp = Blueprint('verses', __name__)

def ensure_upload_folder():
    """اطمینان از وجود پوشه آپلود و ایجاد آن در صورت نیاز"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.isabs(upload_folder):
        # اگر مسیر نسبی است، آن را نسبت به مسیر اصلی پروژه تبدیل به مسیر مطلق می‌کنیم
        upload_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads'))
    
    os.makedirs(upload_folder, exist_ok=True)
    current_app.logger.info(f"Upload folder path: {upload_folder}")
    return upload_folder

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

def allowed_research_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['RESEARCH_IMAGE_ALLOWED_EXTENSIONS']

def get_research_image_upload_folder():
    folder = current_app.config['RESEARCH_IMAGE_UPLOAD_FOLDER']
    os.makedirs(folder, exist_ok=True)
    return folder

from app.models import ResearchImage

@verses_bp.route('/upload_research_image/<int:comment_id>/<int:subtopic_index>', methods=['POST'])
@login_required
def upload_research_image(comment_id, subtopic_index):
    comment = Comment.query.get_or_404(comment_id)
    if not (current_user.id == comment.user_id or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'شما مجوز ندارید.'}), 403

    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'فایل انتخاب نشده است.'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'فایل انتخاب نشده است.'}), 400

    if not allowed_research_image(file.filename):
        return jsonify({'success': False, 'message': 'فرمت فایل مجاز نیست.'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    max_size = current_app.config['RESEARCH_IMAGE_MAX_SIZE_MB'] * 1024 * 1024
    if file_size > max_size:
        return jsonify({'success': False, 'message': f'حجم فایل نباید بیشتر از {current_app.config["RESEARCH_IMAGE_MAX_SIZE_MB"]} مگابایت باشد.'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"comment{comment_id}_subtopic{subtopic_index}_{uuid.uuid4().hex}.{ext}"
    upload_folder = get_research_image_upload_folder()
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    image = ResearchImage(
        comment_id=comment_id,
        subtopic_index=subtopic_index,
        filename=unique_filename,
        original_filename=secure_filename(file.filename),
        file_size=file_size,
        created_at=datetime.utcnow()
    )
    db.session.add(image)
    db.session.commit()
    return jsonify({'success': True, 'image_id': image.id, 'filename': unique_filename})

@verses_bp.route('/delete_research_image/<int:image_id>', methods=['POST'])
@login_required
def delete_research_image(image_id):
    image = ResearchImage.query.get_or_404(image_id)
    comment = image.comment
    if not (current_user.id == comment.user_id or current_user.is_admin()):
        return jsonify({'success': False, 'message': 'شما مجوز ندارید.'}), 403

    file_path = os.path.join(current_app.config['RESEARCH_IMAGE_UPLOAD_FOLDER'], image.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(image)
    db.session.commit()
    return jsonify({'success': True})

@verses_bp.route('/get_research_images/<int:comment_id>/<int:subtopic_index>')
def get_research_images(comment_id, subtopic_index):
    """دریافت تصاویر مربوط به یک زیرموضوع خاص - برای همه کاربران قابل دسترسی"""
    try:
        # دریافت comment
        comment = Comment.query.get_or_404(comment_id)
        
        # دریافت تصاویر از دیتابیس
        images = ResearchImage.query.filter_by(
            comment_id=comment_id, 
            subtopic_index=subtopic_index
        ).all()
        
        images_data = [{
            'id': img.id,
            'filename': img.filename,
            'original_filename': img.original_filename,
            'caption': img.caption or '',
            'file_size': img.file_size,
            'created_at': img.created_at.strftime('%Y-%m-%d %H:%M') if img.created_at else ''
        } for img in images]
        
        return jsonify({
            'success': True,
            'images': images_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting research images: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
            return jsonify({'success': False, 'message': f'اندازه فایل نباید بیشتر از {current_app.config["UPLOAD_MAX_SIZE_MB"]} مگابایت باشد.'})
        
        try:
            # ایجاد نام فایل یکتا
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"garden{title_obj.garden}_poem{title_id}_{current_user.username}_{timestamp}.{file_extension}"
            
            # اطمینان از وجود پوشه آپلود و دریافت مسیر کامل آن
            upload_folder = ensure_upload_folder()
            file_path = os.path.join(upload_folder, unique_filename)
            
            # ذخیره فایل
            file.save(file_path)
            current_app.logger.info(f"File saved to: {file_path}")
            
            if not os.path.exists(file_path):
                raise Exception(f"File was not saved successfully to {file_path}")
            
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
                    'message': 'ضبط صوتی با موفقیت ذخیره شد و در انتظار تأیید مدیر است.'
                })
            
        except Exception as e:
            db.session.rollback()
            # حذف فایل در صورت خطا
            if os.path.exists(file_path):
                os.remove(file_path)
            
            current_app.logger.error(f"Error saving audio file: {e}")
            return jsonify({
                'success': False,
                'message': f'خطا در ذخیره فایل صوتی: {str(e)}'
            })
    
    # برای درخواست GET، صفحه ضبط را نمایش می‌دهیم
    return render_template('verses/record_audio.html', 
                         title=title_obj, 
                         existing_recording=existing_recording)

@verses_bp.route('/play/<int:recording_id>')
def play_audio(recording_id):
    """پخش فایل صوتی"""
    
    recording = Recording.query.get_or_404(recording_id)
    
    # فقط فایل‌های تأیید شده برای همه قابل پخش هستند
    # فایل‌های تأیید نشده فقط برای ادمین‌ها قابل پخش هستند
    if not recording.is_approved and not (current_user.is_authenticated and current_user.is_admin):
        flash('این ضبط صوتی هنوز تأیید نشده است.', 'error')
        return redirect(url_for('main.title', title_id=recording.title_id))
    
    upload_folder = ensure_upload_folder()
    file_path = os.path.join(upload_folder, recording.filename)
    current_app.logger.info(f"Attempting to play file from: {file_path}")
    
    if not os.path.exists(file_path):
        current_app.logger.error(f"Audio file not found at: {file_path}")
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
    
    upload_folder = ensure_upload_folder()
    file_path = os.path.join(upload_folder, recording.filename)
    current_app.logger.info(f"Attempting to download file from: {file_path}")
    
    if not os.path.exists(file_path):
        current_app.logger.error(f"Audio file not found at: {file_path}")
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
    title = Title.query.get_or_404(title_id)
    return render_template('verses/compare_versions.html', title=title)

@verses_bp.route('/get_research_form', methods=['GET'])
@login_required
def get_research_form():
    """دریافت فرم پژوهشی"""
    if current_user.role != 'researcher':
        return jsonify({'error': 'شما دسترسی لازم را ندارید'}), 403
    
    title_id = request.args.get('title_id', type=int)
    if not title_id:
        return jsonify({'error': 'شناسه شعر یافت نشد'}), 400
        
    title = Title.query.get_or_404(title_id)
    
    # بازیابی نظر قبلی کاربر
    existing_comment = Comment.query.filter_by(
        user_id=current_user.id,
        title_id=title_id
    ).first()
    
    comment_data = None
    if existing_comment:
        try:
            comment_data = json.loads(existing_comment.comment)
        except:
            comment_data = None
    
    # دریافت مسیر بازگشت از پارامترهای URL
    return_url = request.args.get('return_url') or url_for('main.title', title_id=title_id)
        
    return render_template('research/researcher_form.html', 
                         title_id=title_id,
                         poem_title=title.title,
                         comment_data=comment_data,
                         comment=existing_comment,
                         return_url=return_url,
                         config=current_app.config)

@verses_bp.route('/submit_research_form/<int:title_id>', methods=['POST'])
@login_required
def submit_research_form(title_id):
    try:
        if current_user.role != 'researcher':
            return jsonify({'success': False, 'message': 'شما مجاز به ثبت فرم پژوهشی نیستید'}), 403
        title = Title.query.get(title_id)
        if not title:
            return jsonify({'success': False, 'message': 'شعر مورد نظر یافت نشد'}), 404
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            data = request.form.to_dict(flat=False)
            # تبدیل مقادیر تک مقداری به مقدار ساده
            for k, v in data.items():
                if isinstance(v, list) and len(v) == 1:
                    data[k] = v[0]
            subtopics = json.loads(data.get('subtopics', '[]'))
            data['subtopics'] = subtopics
            data['user_id'] = current_user.id
            data['title_id'] = title_id
            data['is_admin'] = current_user.is_admin() if hasattr(current_user, 'is_admin') else False
            files = request.files
            # حذف حلقه getlist کپشن
            return_url = data.get('return_url') or url_for('main.title', title_id=title_id)
        else:
            if not request.is_json:
                return jsonify({'success': False, 'message': 'درخواست باید به صورت JSON یا فرم باشد'}), 400
            data = request.get_json()
            data['user_id'] = current_user.id
            data['title_id'] = title_id
            data['is_admin'] = current_user.is_admin() if hasattr(current_user, 'is_admin') else False
            files = None
            return_url = data.get('return_url') or url_for('main.title', title_id=title_id)
        # پیدا کردن comment موجود
        from app.models import Comment
        existing_comment = Comment.query.filter_by(user_id=current_user.id, title_id=title_id).first()
        try:
            comment_obj, message = save_research_form(existing_comment, data, files, current_app.config, is_admin=current_user.is_admin() if hasattr(current_user, 'is_admin') else False)
            return jsonify({'success': True, 'message': message, 'return_url': return_url})
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
        except Exception as e:
            current_app.logger.error(f"Error saving research form: {e}")
            return jsonify({'success': False, 'message': 'خطا در ثبت فرم پژوهشی'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in submit_research_form: {e}")
        return jsonify({'success': False, 'message': 'خطای سیستمی رخ داده است'}), 500

@verses_bp.route('/view_research_comment/<int:comment_id>')
def view_research_comment(comment_id):
    """نمایش نظر پژوهشی در حالت فقط خواندنی"""
    try:
        # دریافت comment
        comment = Comment.query.get_or_404(comment_id)
        
        # دریافت عنوان شعر از relationship
        # فرض می‌کنیم که در model Comment رابطه‌ای با Title وجود دارد
        title_obj = comment.poem_title  # اگر relationship با این نام وجود دارد
        if not title_obj:
            # اگر relationship مستقیم نیست، از title_id استفاده کنیم
            title_obj = Title.query.get(comment.title_id)
        
        if not title_obj:
            flash('شعر مربوط به این نظر یافت نشد', 'error')
            return redirect(url_for('main.index'))
        
        poem_title = title_obj.title
        
        # تبدیل JSON نظر به دیکشنری
        try:
            if isinstance(comment.comment, str):
                comment_data = json.loads(comment.comment)
            elif isinstance(comment.comment, dict):
                comment_data = comment.comment
            else:
                comment_data = {}
        except (json.JSONDecodeError, TypeError):
            current_app.logger.error(f"Error parsing comment JSON for comment_id: {comment_id}")
            comment_data = {
                'subtopics': [],
                'extra_info': '',
                'topic_narrative': '',
                'historical_flaw': '',
                'reform_theory': ''
            }
        
        # اطمینان از وجود کلیدهای مورد نیاز
        default_data = {
            'subtopics': [],
            'extra_info': '',
            'topic_narrative': '',
            'historical_flaw': '',
            'reform_theory': ''
        }
        
        for key, default_value in default_data.items():
            if key not in comment_data:
                comment_data[key] = default_value
        
        # دریافت نام نویسنده نظر
        author_name = comment.author_name if hasattr(comment, 'author_name') and comment.author_name else 'نامشخص'
        if not author_name or author_name == 'نامشخص':
            # اگر author_name خالی است، از user relationship استفاده کنیم
            if hasattr(comment, 'user') and comment.user:
                author_name = comment.user.username
            elif hasattr(comment, 'user_id'):
                user = User.query.get(comment.user_id)
                author_name = user.username if user else 'نامشخص'
        
        # دریافت مسیر بازگشت از پارامترهای URL
        return_url = request.args.get('return_url') or url_for('main.title', title_id=comment.title_id)
        
        # رندر template
        return render_template('research/view_only_form.html', 
                             title_id=comment.title_id,
                             poem_title=poem_title,
                             view_mode=True,
                             comment_data=comment_data,
                             username=author_name,
                             comment=comment,
                             return_url=return_url,
                             config=current_app.config)
        
    except Exception as e:
        current_app.logger.error(f"Error in view_research_comment: {e}")
        flash('خطا در نمایش نظر پژوهشی', 'error')
        return redirect(url_for('main.index'))

@verses_bp.route('/research_image_file/<path:filename>')
def research_image_file(filename):
    """سرو کردن فایل‌های تصویری پژوهشی"""
    try:
        folder = current_app.config['RESEARCH_IMAGE_UPLOAD_FOLDER']
        
        # بررسی امنیتی نام فایل
        secure_name = secure_filename(filename)
        if secure_name != filename:
            current_app.logger.warning(f"Insecure filename attempted: {filename}")
            return "فایل نامعتبر", 400
        
        # بررسی وجود فایل
        file_path = os.path.join(folder, filename)
        if not os.path.exists(file_path):
            current_app.logger.warning(f"Research image file not found: {file_path}")
            return "فایل یافت نشد", 404
            
        return send_from_directory(folder, filename)
        
    except Exception as e:
        current_app.logger.error(f"Error serving research image: {e}")
        return "خطا در بارگذاری تصویر", 500