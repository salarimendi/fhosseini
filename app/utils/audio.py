"""
فایل کمکی برای مدیریت فایل‌های صوتی
Audio utilities for managing recordings
"""
import os
from werkzeug.utils import secure_filename

# تنظیمات فایل صوتی
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'aac', 'm4a'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 مگابایت

def allowed_file(filename):
    """بررسی نوع فایل مجاز"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_audio_file(file, user_id, title_id):
    """ذخیره فایل صوتی با نام امن"""
    if file and allowed_file(file.filename):
        # ایجاد نام فایل امن
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        
        # نام جدید فایل: user_id_title_id.extension
        new_filename = f"user_{user_id}_title_{title_id}.{extension}"
        
        # مسیر ذخیره
        upload_folder = os.path.join('app', 'static', 'audio')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, new_filename)
        
        try:
            file.save(file_path)
            return new_filename
        except Exception as e:
            print(f"خطا در ذخیره فایل: {e}")
            return None
    
    return None

def delete_audio_file(filename):
    """حذف فایل صوتی"""
    try:
        file_path = os.path.join('app', 'static', 'audio', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"خطا در حذف فایل: {e}")
    return False

def get_audio_url(filename):
    """دریافت URL فایل صوتی"""
    if filename:
        return f"/static/audio/{filename}"
    return None

def validate_file_size(file):
    """اعتبارسنجی حجم فایل"""
    if not file:
        return False
    
    # بررسی حجم فایل
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # برگشت به ابتدای فایل
    
    return file_size <= MAX_FILE_SIZE