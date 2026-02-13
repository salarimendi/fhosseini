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

def format_verse_versions(verse):
    """
    تنسیق و آماده‌سازی اطلاعات نسخ‌های موجود برای نمایش
    Returns formatted versions info or None
    """
    if not verse.present_in_versions:
        return None
    return verse.present_in_versions.strip()

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
    ذخیره یا ویرایش فرم پژوهشی (فقط زیرموضوعات و فیلدهای متنی)
    مدیریت عکس‌ها به صورت جداگانه انجام می‌شود
    """
    import json
    from datetime import datetime
    from app import db

    subtopics = data.get('subtopics', [])
    extra_info = data.get('extra_info', '')
    topic_narrative = data.get('topic_narrative', '')
    
    # فیلدهای جدید نظریه پژوهشی
    primary_theory = data.get('primary_theory', '')
    review_theory = data.get('review_theory', '')
    final_theory = data.get('final_theory', '')

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
        'primary_theory': primary_theory,
        'review_theory': review_theory,
        'final_theory': final_theory,
        'form_type': 'research_form'
    }

    if comment_obj:
        # ویرایش نظر موجود
        comment_obj.comment = json.dumps(research_data, ensure_ascii=False)
        comment_obj.updated_at = datetime.utcnow()
        if not is_admin:
            comment_obj.status = 'pending'
            message = 'فرم پژوهشی با موفقیت ویرایش شد و در انتظار تأیید مجدد است'
        else:
            message = 'فرم پژوهشی با موفقیت ویرایش شد'
    else:
        # ایجاد نظر جدید
        from app.models import Comment
        comment_obj = Comment(
            user_id=data['user_id'],
            title_id=data['title_id'],
            comment=json.dumps(research_data, ensure_ascii=False),
            status='approved' if is_admin or data.get('is_admin') else 'pending'
        )
        db.session.add(comment_obj)
    
    db.session.commit()
    return comment_obj, message



##### توابع جدید برای فرم عکس

def get_subtopic_images(comment_id, subtopic_index):
    """دریافت تصاویر یک زیرموضوع خاص"""
    from app.models import ResearchImage
    return ResearchImage.query.filter_by(
        comment_id=comment_id,
        subtopic_index=subtopic_index
    ).order_by(ResearchImage.created_at).all()

def delete_all_subtopic_images(comment_id, subtopic_index):
    """حذف تمام تصاویر یک زیرموضوع"""
    import os
    from flask import current_app
    from app.models import ResearchImage
    
    images = ResearchImage.query.filter_by(
        comment_id=comment_id,
        subtopic_index=subtopic_index
    ).all()
    
    folder = current_app.config['RESEARCH_IMAGE_UPLOAD_FOLDER']
    
    for image in images:
        # حذف فایل فیزیکی
        file_path = os.path.join(folder, image.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting image file {file_path}: {e}")
        
        # حذف رکورد از دیتابیس
        db.session.delete(image)
    
    db.session.commit()

def validate_image_access(image_id, user_id, is_admin=False):
    """بررسی دسترسی کاربر به یک تصویر"""
    from app.models import ResearchImage
    
    image = ResearchImage.query.get(image_id)
    if not image:
        return None, "تصویر یافت نشد"
    
    comment = image.comment
    if not (user_id == comment.user_id or is_admin):
        return None, "شما مجوز دسترسی به این تصویر را ندارید"
    
    return image, None


def get_comments_filtered(page=1, per_page=20, search='', status='', garden=None, order=None):
    """
    دریافت نظرات با فیلترهای مختلف
    """
    query = Comment.query.join(Title, Comment.title_id == Title.id, isouter=True)
    
    # فیلتر جستجو
    if search:
        query = query.join(User).filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                Comment.comment.ilike(f'%{search}%')
            )
        )
    
    # فیلتر وضعیت
    if status:
        query = query.filter(Comment.status == status)
    
    # فیلتر باغ
    if garden is not None:
        query = query.filter(Title.garden == garden)
    
    # فیلتر ترتیب
    if order is not None:
        query = query.filter(Title.order_in_garden == order)
    
    return query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

def get_available_gardens():
    """
    دریافت لیست باغ‌های موجود با تعداد اشعار
    """
    from sqlalchemy import func
    return db.session.query(
        Title.garden,
        func.count(db.distinct(Title.id)).label('poems_count')
    ).group_by(Title.garden).order_by(Title.garden).all()


# =============================================================================
# توابع جدید برای سیستم نظرات تصحیحی ابیات
# این کد باید به انتهای فایل database.py اضافه شود
# =============================================================================

def get_verse_corrections(verse_id, include_pending=False, user_id=None):
    """
    دریافت نظرات تصحیحی یک بیت
    
    Args:
        verse_id: شناسه بیت
        include_pending: نمایش نظرات در انتظار (برای ادمین)
        user_id: شناسه کاربر (برای نمایش نظرات خود کاربر)
    
    Returns:
        لیست نظرات تصحیحی با اطلاعات کامل
    """
    from app.models import VerseCorrection, User
    
    query = VerseCorrection.query.filter_by(verse_id=verse_id)
    
    if include_pending:
        # برای ادمین: همه نظرات
        corrections = query.order_by(VerseCorrection.created_at.desc()).all()
    elif user_id:
        # برای کاربر: نظرات تایید شده + نظرات خودش
        corrections = query.filter(
            or_(
                VerseCorrection.is_approved == True,
                VerseCorrection.created_by == user_id
            )
        ).order_by(VerseCorrection.created_at.desc()).all()
    else:
        # برای مهمان: فقط نظرات تایید شده
        corrections = query.filter_by(is_approved=True)\
            .order_by(VerseCorrection.created_at.desc()).all()
    
    # اضافه کردن اطلاعات کاربر
    result = []
    for correction in corrections:
        user = User.query.get(correction.created_by)
        approver = User.query.get(correction.approved_by) if correction.approved_by else None
        
        result.append({
            'id': correction.id,
            'verse_id': correction.verse_id,
            'field_name': correction.field_name,
            'old_text': correction.old_text,
            'new_text': correction.new_text,
            'correction_type': correction.correction_type,
            'note': correction.note,
            'created_by': correction.created_by,
            'created_by_name': user.username if user else 'ناشناس',
            'created_by_fullname': user.fullname if user else 'ناشناس',
            'created_at': correction.created_at,
            'is_approved': correction.is_approved,
            'approved_by_name': approver.username if approver else None,
            'approved_at': correction.approved_at
        })
    
    return result


def save_verse_correction(data, user_id):
    """
    ذخیره یا ویرایش نظر تصحیحی
    
    Args:
        data: دیکشنری حاوی اطلاعات نظر تصحیحی
        user_id: شناسه کاربر
    
    Returns:
        tuple: (correction_object, message)
    
    Raises:
        ValueError: در صورت اعتبارسنجی ناموفق
    """
    from app.models import VerseCorrection, Verse
    from datetime import datetime
    
    # اعتبارسنجی
    verse_id = data.get('verse_id')
    if not verse_id:
        raise ValueError('شناسه بیت الزامی است')
    
    verse = Verse.query.get(verse_id)
    if not verse:
        raise ValueError('بیت مورد نظر یافت نشد')
    
    # field_name - اگر ارسال نشده باشد، مقدار پیش‌فرض استفاده کن
    field_name = data.get('field_name')
    valid_fields = ['verse_1', 'verse_2', 'verse_1_tag', 'verse_2_tag', 'variant_diff', 'present_in_versions']
    if not field_name:
        field_name = 'verse_1'  # مقدار پیش‌فرض
    elif field_name not in valid_fields:
        raise ValueError('فیلد انتخاب شده نامعتبر است')
    
    new_text = data.get('new_text', '').strip()
    if not new_text:
        raise ValueError('متن پیشنهادی نمی‌تواند خالی باشد')
    
    correction_type = data.get('correction_type', 'text')
    note = data.get('note', '').strip()
    
    # دریافت متن فعلی
    old_text = getattr(verse, field_name, None) or ''
    
    # بررسی تکراری نبودن - هر کاربر فقط یک نظر برای هر بیت
    correction_id = data.get('correction_id')
    if not correction_id:
        existing = VerseCorrection.query.filter_by(
            verse_id=verse_id,
            created_by=user_id,
            is_approved=False
        ).first()
        
        if existing:
            raise ValueError('شما قبلاً برای این بیت نظر ثبت کرده‌اید که هنوز تایید نشده است. لطفاً نظر قبلی را ویرایش کنید یا منتظر تایید آن بمانید.')
    
    if correction_id:
        # ویرایش
        correction = VerseCorrection.query.get(correction_id)
        if not correction:
            raise ValueError('نظر مورد نظر یافت نشد')
        
        if correction.created_by != user_id:
            raise ValueError('شما مجوز ویرایش این نظر را ندارید')
        
        if correction.is_approved:
            raise ValueError('نظرات تایید شده قابل ویرایش نیستند')
        
        correction.old_text = old_text
        correction.new_text = new_text
        correction.correction_type = correction_type
        correction.note = note
        message = 'نظر تصحیحی با موفقیت ویرایش شد'
    else:
        # ایجاد جدید
        correction = VerseCorrection(
            verse_id=verse_id,
            field_name=field_name,
            old_text=old_text,
            new_text=new_text,
            correction_type=correction_type,
            note=note,
            created_by=user_id,
            is_approved=False
        )
        db.session.add(correction)
        message = 'نظر تصحیحی با موفقیت ثبت شد و پس از تایید مدیر نمایش داده خواهد شد'
    
    db.session.commit()
    return correction, message


def delete_verse_correction(correction_id, user_id, is_admin=False):
    """
    حذف نظر تصحیحی
    
    Args:
        correction_id: شناسه نظر
        user_id: شناسه کاربر
        is_admin: آیا کاربر ادمین است
    
    Returns:
        str: پیام موفقیت
    
    Raises:
        ValueError: در صورت عدم دسترسی یا یافت نشدن نظر
    """
    from app.models import VerseCorrection
    
    correction = VerseCorrection.query.get(correction_id)
    if not correction:
        raise ValueError('نظر مورد نظر یافت نشد')
    
    # بررسی مجوز
    if not is_admin and correction.created_by != user_id:
        raise ValueError('شما مجوز حذف این نظر را ندارید')
    
    db.session.delete(correction)
    db.session.commit()
    return 'نظر تصحیحی با موفقیت حذف شد'


def user_can_add_correction(user_id, verse_id, field_name):
    """
    بررسی اینکه آیا کاربر می‌تواند نظر جدید اضافه کند
    (یک کاربر نمی‌تواند برای یک فیلد چند نظر pending داشته باشد)
    
    Args:
        user_id: شناسه کاربر
        verse_id: شناسه بیت
        field_name: نام فیلد
    
    Returns:
        bool: امکان افزودن نظر جدید
    """
    from app.models import VerseCorrection
    
    # بررسی نظر pending قبلی
    existing = VerseCorrection.query.filter_by(
        verse_id=verse_id,
        field_name=field_name,
        created_by=user_id,
        is_approved=False
    ).first()
    
    return existing is None


def get_pending_corrections_count():
    """
    تعداد نظرات تصحیحی در انتظار تایید
    
    Returns:
        int: تعداد نظرات pending
    """
    from app.models import VerseCorrection
    return VerseCorrection.query.filter_by(is_approved=False).count()


def get_corrections_filtered(page=1, per_page=20, status='', search=''):
    """
    دریافت نظرات تصحیحی با فیلتر برای پنل مدیریت
    
    Args:
        page: شماره صفحه
        per_page: تعداد در هر صفحه
        status: فیلتر وضعیت ('approved', 'pending', یا '')
        search: متن جستجو
    
    Returns:
        Pagination object
    """
    from app.models import VerseCorrection, Verse, Title, User
    
    query = VerseCorrection.query.join(Verse).join(Title)
    
    # فیلتر وضعیت
    if status == 'approved':
        query = query.filter(VerseCorrection.is_approved == True)
    elif status == 'pending':
        query = query.filter(VerseCorrection.is_approved == False)
    
    # فیلتر جستجو
    if search:
        query = query.join(User, VerseCorrection.created_by == User.id).filter(
            or_(
                User.username.ilike(f'%{search}%'),
                VerseCorrection.new_text.ilike(f'%{search}%'),
                VerseCorrection.note.ilike(f'%{search}%'),
                Title.title.ilike(f'%{search}%')
            )
        )
    
    return query.order_by(VerseCorrection.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def approve_verse_correction(correction_id, admin_id):
    """
    تایید نظر تصحیحی توسط ادمین
    
    Args:
        correction_id: شناسه نظر
        admin_id: شناسه ادمین
    
    Returns:
        str: پیام موفقیت
    
    Raises:
        ValueError: در صورت یافت نشدن یا تایید قبلی
    """
    from app.models import VerseCorrection
    from datetime import datetime, UTC
    
    correction = VerseCorrection.query.get(correction_id)
    if not correction:
        raise ValueError('نظر مورد نظر یافت نشد')
    
    if correction.is_approved:
        raise ValueError('این نظر قبلاً تایید شده است')
    
    correction.is_approved = True
    correction.approved_by = admin_id
    correction.approved_at = datetime.now(UTC)
    
    db.session.commit()
    return 'نظر تصحیحی با موفقیت تایید شد'


def reject_verse_correction(correction_id):
    """
    رد نظر تصحیحی (حذف)
    
    Args:
        correction_id: شناسه نظر
    
    Returns:
        str: پیام موفقیت
    
    Raises:
        ValueError: در صورت یافت نشدن نظر
    """
    from app.models import VerseCorrection
    
    correction = VerseCorrection.query.get(correction_id)
    if not correction:
        raise ValueError('نظر مورد نظر یافت نشد')
    
    db.session.delete(correction)
    db.session.commit()
    return 'نظر تصحیحی رد و حذف شد'


# =============================================================================
# پایان توابع نظرات تصحیحی
# =============================================================================

# =============================================================================
# تابع انتخاب بیت روزانه
# =============================================================================

def get_daily_verse():
    """
    انتخاب یک بیت تصادفی از تمام ابیات
    
    Returns:
        dict: حاوی اطلاعات بیت تصادفی
            {
                'verse': Verse object,
                'title': Title object,
                'verse_1': str,
                'verse_2': str,
                'garden': int,
                'title_name': str,
                'title_id': int,
                'verse_id': int,
                'title_order_in_garden': int,
                'verse_order_in_title': int
            }
    """
    from app.models import Verse, Title
    from sqlalchemy import func
    
    # دریافت بیت تصادفی
    verse = Verse.query.order_by(func.random()).limit(1).first()
    
    if not verse:
        return None
    
    # دریافت عنوان شعر
    title = Title.query.get(verse.title_id)
    
    return {
        'verse': verse,
        'title': title,
        'verse_1': verse.verse_1,
        'verse_2': verse.verse_2,
        'garden': title.garden if title else None,
        'title_name': title.title if title else 'نامعلوم',
        'title_id': title.id if title else None,
        'verse_id': verse.id,
        'garden_name': title.garden_name if title else 'نامعلوم',
        'title_order_in_garden': title.order_in_garden if title else None,
        'verse_order_in_title': verse.order_in_title if verse else None
    }