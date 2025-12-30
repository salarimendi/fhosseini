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
        comment_obj.status = 'pending'  # وضعیت به منتظر تایید برمی‌گردد
        message = 'فرم پژوهشی با موفقیت ویرایش شد و در انتظار تأیید مجدد است'
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