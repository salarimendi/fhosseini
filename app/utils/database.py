"""
فایل کمکی برای مدیریت پایگاه داده
Database utilities and helper functions
"""
from app import db
from app.models import Title, Verse, User, Comment, Recording
from sqlalchemy import or_

def search_in_database(query):
    """جستجو در تیترها و ابیات"""
    if not query:
        return []
    
    search_term = f"%{query}%"
    
    # جستجو در تیترها
    titles = Title.query.filter(Title.title.like(search_term)).all()
    
    # جستجو در ابیات
    verses = Verse.query.filter(
        or_(
            Verse.verse_1.like(search_term),
            Verse.verse_2.like(search_term)
        )
    ).all()
    
    results = []
    
    # اضافه کردن نتایج تیترها
    for title in titles:
        results.append({
            'type': 'title',
            'id': title.id,
            'title': title.title,
            'garden': title.garden,
            'match': title.title
        })
    
    # اضافه کردن نتایج ابیات
    for verse in verses:
        title = Title.query.get(verse.title_id)
        match_text = verse.verse_1
        # اصلاح بررسی verse_2 برای جلوگیری از خطا
        if verse.verse_2 and query.lower() in verse.verse_2.lower():
            match_text = verse.verse_2
            
        results.append({
            'type': 'verse',
            'id': verse.id,
            'title_id': verse.title_id,
            'title': title.title if title else 'نامشخص',
            'garden': title.garden if title else 0,
            'match': match_text,
            'order': verse.order_in_title
        })
    
    return results

def get_garden_titles(garden_number):
    """دریافت تیترهای یک باغ"""
    return Title.query.filter_by(garden=garden_number)\
                     .order_by(Title.order_in_garden).all()

def get_title_verses(title_id):
    """دریافت ابیات یک تیتر"""
    return Verse.query.filter_by(title_id=title_id)\
                     .order_by(Verse.order_in_title).all()

def get_title_comments(title_id):
    """دریافت نظرات یک تیتر"""
    return Comment.query.filter_by(title_id=title_id)\
                       .order_by(Comment.created_at).all()

def get_title_recordings(title_id):
    """دریافت ضبط‌های صوتی یک تیتر"""
    recordings = Recording.query.filter_by(title_id=title_id).all()
    result = []
    
    for recording in recordings:
        user = User.query.get(recording.user_id)
        result.append({
            'id': recording.id,
            'filename': recording.filename,
            'user_name': user.username if user else 'نامشخص',
            'created_at': recording.created_at,
            'is_approved': recording.is_approved
        })
    
    return result

def user_has_recording_for_title(user_id, title_id):
    """بررسی اینکه آیا کاربر قبلاً برای این تیتر ضبط کرده"""
    return Recording.query.filter_by(
        user_id=user_id, 
        title_id=title_id
    ).first() is not None

def user_has_comment_for_title(user_id, title_id):
    """بررسی اینکه آیا کاربر قبلاً برای این تیتر نظر داده"""
    return Comment.query.filter_by(
        user_id=user_id, 
        title_id=title_id
    ).first() is not None

def get_gardens_info():
    """دریافت اطلاعات باغ‌ها"""
    gardens = {}
    titles = Title.query.all()
    
    for title in titles:
        garden_num = title.garden
        if garden_num not in gardens:
            gardens[garden_num] = {
                'number': garden_num,
                'count': 0,
                'name': title.garden_name  # استفاده از property در مدل
            }
        gardens[garden_num]['count'] += 1
    
    return sorted(gardens.values(), key=lambda x: x['number'])

def get_garden_name(garden_number):
    """دریافت نام باغ بر اساس شماره"""
    garden_names = {
        1: 'خیابان اول باغ فردوس',
        2: 'خیابان دوم باغ فردوس', 
        3: 'خیابان سوم باغ فردوس',
        4: 'خیابان چهارم باغ فردوس'
    }
    return garden_names.get(garden_number, f'باغ {garden_number}')

def get_statistics():
    """دریافت آمار کلی سایت"""
    stats = {
        'total_titles': Title.query.count(),
        'total_verses': Verse.query.count(),
        'total_users': User.query.count(),
        'total_comments': Comment.query.count(),
        'total_recordings': Recording.query.count(),
        'approved_comments': Comment.query.filter_by(is_approved=True).count(),
        'approved_recordings': Recording.query.filter_by(is_approved=True).count(),
        'gardens_count': len(set([t.garden for t in Title.query.all()]))
    }
    return stats

def save_research_form(comment_obj, data, files, config, is_admin=False):
    """
    ذخیره یا ویرایش فرم پژوهشی (زیرموضوعات، عکس‌ها و ...)
    comment_obj: شیء Comment موجود یا None برای ایجاد جدید
    data: dict داده‌های فرم (subtopics, extra_info, ...)
    files: request.files
    config: current_app.config
    is_admin: اگر True باشد یعنی ادمین ویرایش می‌کند
    خروجی: (comment_obj, message)
    """
    import os, uuid, json
    from datetime import datetime
    from werkzeug.utils import secure_filename
    from app import db
    from app.models import ResearchImage

    subtopics = data.get('subtopics', [])
    extra_info = data.get('extra_info', '')
    topic_narrative = data.get('topic_narrative', '')
    historical_flaw = data.get('historical_flaw', '')
    reform_theory = data.get('reform_theory', '')

    # اعتبارسنجی داده‌ها
    if not isinstance(subtopics, list):
        raise ValueError('فرمت داده‌های ارسالی نامعتبر است')
    if not subtopics:
        raise ValueError('حداقل یک زیر موضوع باید وارد شود')
    for subtopic in subtopics:
        if not isinstance(subtopic, dict):
            raise ValueError('فرمت زیر موضوع نامعتبر است')
        if not subtopic.get('title'):
            raise ValueError('عنوان زیر موضوع نمی‌تواند خالی باشد')

    research_data = {
        'subtopics': [{ 'title': s.get('title'), 'sources': s.get('sources', '') } for s in subtopics],
        'extra_info': extra_info,
        'topic_narrative': topic_narrative,
        'historical_flaw': historical_flaw,
        'reform_theory': reform_theory,
        'form_type': 'research_form'
    }

    if comment_obj:
        # ویرایش نظر موجود
        comment_obj.comment = json.dumps(research_data, ensure_ascii=False)
        comment_obj.updated_at = datetime.utcnow()
        message = 'فرم پژوهشی با موفقیت ویرایش شد'
    else:
        # ایجاد نظر جدید (باید user_id و title_id ست شود قبل از فراخوانی این تابع)
        from app.models import Comment
        comment_obj = Comment(
            user_id=data['user_id'],
            title_id=data['title_id'],
            comment=json.dumps(research_data, ensure_ascii=False),
            status='approved' if is_admin or data.get('is_admin') else 'pending'
        )
        db.session.add(comment_obj)
        db.session.flush()  # تا id داشته باشیم
        message = 'فرم پژوهشی با موفقیت ثبت شد' + ('' if is_admin else ' و پس از تأیید نمایش داده خواهد شد')

    # اضافه کردن عکس‌های جدید و به‌روزرسانی کپشن‌های عکس‌های موجود
    for idx, subtopic in enumerate(subtopics):
        # پردازش عکس‌های جدید
        img_files = files.getlist(f'images_{idx}[]') if files else []
        captions = data.get(f'captions_{idx}[]', [])
        if not isinstance(captions, list):
            # اگر فقط یک مقدار است
            captions = [captions]
        for i, file in enumerate(img_files):
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                allowed_exts = config['RESEARCH_IMAGE_ALLOWED_EXTENSIONS']
                if ext not in allowed_exts:
                    continue
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                max_size = config['RESEARCH_IMAGE_MAX_SIZE_MB'] * 1024 * 1024
                if file_size > max_size:
                    continue
                unique_filename = f"comment{comment_obj.id}_subtopic{idx}_{uuid.uuid4().hex}.{ext}"
                upload_folder = config['RESEARCH_IMAGE_UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                caption = captions[i] if i < len(captions) else ''
                image = ResearchImage(
                    comment_id=comment_obj.id,
                    subtopic_index=idx,
                    filename=unique_filename,
                    original_filename=secure_filename(file.filename),
                    caption=caption,
                    file_size=file_size,
                    created_at=datetime.utcnow()
                )
                db.session.add(image)
        
        # به‌روزرسانی کپشن‌های عکس‌های موجود
        existing_captions = data.get(f'existing_captions_{idx}[]', [])
        existing_image_ids = data.get(f'existing_image_ids_{idx}[]', [])
        if not isinstance(existing_captions, list):
            existing_captions = [existing_captions]
        if not isinstance(existing_image_ids, list):
            existing_image_ids = [existing_image_ids]
        
        for i, image_id in enumerate(existing_image_ids):
            if i < len(existing_captions):
                # به‌روزرسانی کپشن عکس موجود
                existing_image = ResearchImage.query.filter_by(
                    id=image_id, 
                    comment_id=comment_obj.id
                ).first()
                if existing_image:
                    existing_image.caption = existing_captions[i]
    db.session.commit()
    return comment_obj, message