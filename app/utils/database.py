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