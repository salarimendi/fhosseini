import json
import os
from datetime import datetime
from flask import current_app

def get_visit_file_path():
    """مسیر فایل آمار بازدید را برمی‌گرداند"""
    instance_path = current_app.instance_path
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    return os.path.join(instance_path, 'daily_visits.json')

def load_visit_data():
    """داده‌های بازدید را از فایل JSON بارگذاری می‌کند"""
    visit_file = get_visit_file_path()
    
    if not os.path.exists(visit_file):
        return {}
    
    try:
        with open(visit_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # اطمینان از اینکه داده‌ها dictionary است
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, IOError, OSError) as e:
        current_app.logger.error(f"خطا در خواندن فایل آمار بازدید: {e}")
        return {}

def save_visit_data(data):
    """داده‌های بازدید را در فایل JSON ذخیره می‌کند"""
    visit_file = get_visit_file_path()
    
    try:
        with open(visit_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, OSError) as e:
        current_app.logger.error(f"خطا در ذخیره فایل آمار بازدید: {e}")
        return False

def increment_visit():
    """تعداد بازدید امروز را یک واحد افزایش می‌دهد"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    data = load_visit_data()
    data[today] = data.get(today, 0) + 1
    
    if save_visit_data(data):
        return data[today]
    return 0

def get_today_visits():
    """تعداد بازدید امروز را برمی‌گرداند"""
    today = datetime.now().strftime('%Y-%m-%d')
    data = load_visit_data()
    return data.get(today, 0)

def get_total_visits():
    """مجموع کل بازدیدها را برمی‌گرداند"""
    data = load_visit_data()
    if not data:
        return 0
    
    total = 0
    for date_str, visits in data.items():
        if isinstance(visits, int) and visits > 0:
            total += visits
    
    return total

def get_visit_stats():
    """آمار کامل بازدیدها را برمی‌گرداند"""
    return {
        'today_visits': get_today_visits(),
        'total_visits': get_total_visits()
    }
