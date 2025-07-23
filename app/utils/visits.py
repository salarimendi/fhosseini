import json
import os
from datetime import datetime

VISIT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'instance', 'daily_visits.json')


def increment_visit():
    today = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(VISIT_FILE):
        data = {}
    else:
        with open(VISIT_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    data[today] = data.get(today, 0) + 1
    with open(VISIT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return data[today]


def get_today_visits():
    today = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(VISIT_FILE):
        return 0
    with open(VISIT_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return 0
    return data.get(today, 0)


def get_total_visits():
    if not os.path.exists(VISIT_FILE):
        return 0
    with open(VISIT_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception:
            return 0
    return sum(data.values()) 