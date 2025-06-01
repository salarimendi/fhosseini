"""
فایل کمکی برای مدیریت نسخه‌های مختلف اشعار
Versioning utilities for different text versions
"""
from app import db
from app.models import Version, VersionVerse, Title

def get_all_versions():
    """دریافت تمام نسخه‌ها"""
    return Version.query.all()

def get_version_verses(version_id, title_id):
    """دریافت ابیات یک نسخه برای تیتر مشخص"""
    return VersionVerse.query.filter_by(
        version_id=version_id,
        title_id=title_id
    ).order_by(VersionVerse.order_in_title).all()

def create_version(name, description=None):
    """ایجاد نسخه جدید"""
    try:
        version = Version(name=name, description=description)
        db.session.add(version)
        db.session.commit()
        return version
    except Exception as e:
        db.session.rollback()
        print(f"خطا در ایجاد نسخه: {e}")
        return None

def add_verse_to_version(version_id, title_id, order_in_title, verse_1, verse_2=None):
    """اضافه کردن بیت به نسخه"""
    try:
        version_verse = VersionVerse(
            version_id=version_id,
            title_id=title_id,
            order_in_title=order_in_title,
            verse_1=verse_1,
            verse_2=verse_2
        )
        db.session.add(version_verse)
        db.session.commit()
        return version_verse
    except Exception as e:
        db.session.rollback()
        print(f"خطا در اضافه کردن بیت به نسخه: {e}")
        return None

def compare_versions(version1_id, version2_id, title_id):
    """مقایسه دو نسخه برای یک تیتر"""
    version1_verses = get_version_verses(version1_id, title_id)
    version2_verses = get_version_verses(version2_id, title_id)
    
    comparison = {
        'version1': {
            'id': version1_id,
            'verses': version1_verses
        },
        'version2': {
            'id': version2_id, 
            'verses': version2_verses
        },
        'differences': []
    }
    
    # پیدا کردن تفاوت‌ها
    max_verses = max(len(version1_verses), len(version2_verses))
    
    for i in range(max_verses):
        v1_verse = version1_verses[i] if i < len(version1_verses) else None
        v2_verse = version2_verses[i] if i < len(version2_verses) else None
        
        if not v1_verse or not v2_verse:
            comparison['differences'].append({
                'order': i + 1,
                'type': 'missing',
                'verse1': v1_verse,
                'verse2': v2_verse
            })
        elif (v1_verse.verse_1 != v2_verse.verse_1 or 
              v1_verse.verse_2 != v2_verse.verse_2):
            comparison['differences'].append({
                'order': i + 1,
                'type': 'different',
                'verse1': v1_verse,
                'verse2': v2_verse
            })
    
    return comparison

def get_version_statistics(version_id):
    """دریافت آمار یک نسخه"""
    version = Version.query.get(version_id)
    if not version:
        return None
    
    verses_count = VersionVerse.query.filter_by(version_id=version_id).count()
    titles_count = len(set([vv.title_id for vv in 
                           VersionVerse.query.filter_by(version_id=version_id).all()]))
    
    return {
        'version': version,
        'verses_count': verses_count,
        'titles_count': titles_count
    }

def delete_version(version_id):
    """حذف نسخه و تمام ابیات آن"""
    try:
        # حذف ابیات نسخه
        VersionVerse.query.filter_by(version_id=version_id).delete()
        
        # حذف نسخه
        version = Version.query.get(version_id)
        if version:
            db.session.delete(version)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"خطا در حذف نسخه: {e}")
        return False

def copy_main_to_version(version_id):
    """کپی کردن ابیات اصلی به نسخه"""
    try:
        from app.models import Verse
        
        # حذف ابیات قبلی این نسخه
        VersionVerse.query.filter_by(version_id=version_id).delete()
        
        # کپی ابیات اصلی
        main_verses = Verse.query.all()
        
        for verse in main_verses:
            version_verse = VersionVerse(
                version_id=version_id,
                title_id=verse.title_id,
                order_in_title=verse.order_in_title,
                verse_1=verse.verse_1,
                verse_2=verse.verse_2
            )
            db.session.add(version_verse)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"خطا در کپی ابیات اصلی: {e}")
        return False