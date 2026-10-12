from datetime import datetime
def increment_visit():
    """تعداد بازدید امروز را یک واحد افزایش می‌دهد (دیتابیس)"""
    from app import db
    from app.models import Visit
    today = datetime.now().strftime('%Y-%m-%d')
    visit = Visit.query.filter_by(date=today).first()
    if not visit:
        visit = Visit(date=today, count=1)
        db.session.add(visit)
    else:
        visit.count += 1
    db.session.commit()
    return visit.count

def get_today_visits():
    """تعداد بازدید امروز را برمی‌گرداند (دیتابیس)"""
    from app.models import Visit
    today = datetime.now().strftime('%Y-%m-%d')
    visit = Visit.query.filter_by(date=today).first()
    return visit.count if visit else 0

def get_total_visits():
    """مجموع کل بازدیدها را برمی‌گرداند (دیتابیس)"""
    from app import db
    from app.models import Visit
    total = db.session.query(db.func.sum(Visit.count)).scalar()
    return total if total else 0

def get_visit_stats():
    return {
        'today_visits': get_today_visits(),
        'total_visits': get_total_visits()
    }
