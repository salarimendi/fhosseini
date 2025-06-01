#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای اصلی پروژه فردوسی حسینی
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import or_
from app.models import Title, Verse, SearchResult
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """صفحه اصلی - نمایش باغ‌ها"""
    
    # دریافت آمار کلی
    stats = {
        'total_poems': Title.query.count(),
        'total_verses': Verse.query.count(),
        'gardens': []
    }
    
    # آمار هر باغ
    for garden_num in range(1, 5):
        garden_titles = Title.query.filter_by(garden=garden_num).count()
        garden_name = {
            1: 'خیابان اول باغ فردوس',
            2: 'خیابان دوم باغ فردوس',
            3: 'خیابان سوم باغ فردوس',
            4: 'خیابان چهارم باغ فردوس'
        }[garden_num]
        
        stats['gardens'].append({
            'number': garden_num,
            'name': garden_name,
            'title_count': garden_titles
        })
    
    return render_template('home.html', stats=stats)

@main_bp.route('/garden/<int:garden_id>')
def garden(garden_id):
    """نمایش عناوین یک باغ خاص"""
    
    if garden_id < 1 or garden_id > 4:
        return "باغ مورد نظر یافت نشد.", 404
    
    # دریافت عناوین باغ مرتب شده
    titles = Title.query.filter_by(garden=garden_id)\
                       .order_by(Title.order_in_garden)\
                       .all()
    
    garden_name = {
        1: 'خیابان اول باغ فردوس',
        2: 'خیابان دوم باغ فردوس',
        3: 'خیابان سوم باغ فردوس',
        4: 'خیابان چهارم باغ فردوس'
    }[garden_id]
    
    return render_template('garden.html', 
                         titles=titles, 
                         garden_id=garden_id,
                         garden_name=garden_name)

@main_bp.route('/title/<int:title_id>')
def title(title_id):
    """نمایش شعر کامل با ابیات و نظرات"""
    
    title_obj = Title.query.get_or_404(title_id)
    
    # دریافت ابیات مرتب شده
    verses = title_obj.get_verses_ordered()
    
    # دریافت نظرات تأیید شده
    comments = title_obj.get_comments()
    approved_comments = [c for c in comments if c.is_approved]
    
    # دریافت ضبط‌های صوتی تأیید شده
    recordings = []
    for recording in title_obj.recordings:
        if recording.is_approved:
            recordings.append({
                'id': recording.id,
                'reader_name': recording.user.username,
                'filename': recording.filename,
                'file_path': recording.file_path,
                'duration': recording.duration,
                'created_at': recording.created_at
            })
    
    return render_template('title.html',
                         title=title_obj,
                         verses=verses,
                         comments=approved_comments,
                         recordings=recordings)

@main_bp.route('/search')
def search():
    """جستجو در عناوین و ابیات"""
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'message': 'لطفاً کلمه کلیدی وارد کنید.'})
    
    results = []
    
    # جستجو در عناوین
    title_results = Title.query.filter(Title.title.contains(query)).all()
    for title in title_results:
        results.append(SearchResult(
            title=title.title,
            content=f"از {title.garden_name}",
            url=f"/title/{title.id}",
            type_name="عنوان شعر"
        ))
    
    # جستجو در ابیات
    verse_results = Verse.query.filter(
        or_(Verse.verse_1.contains(query), 
            Verse.verse_2.contains(query))
    ).limit(20).all()
    
    for verse in verse_results:
        # نمایش بیت حاوی کلمه جستجو
        content = verse.verse_1
        if verse.verse_2 and query in verse.verse_2:
            content = verse.verse_2
        
        results.append(SearchResult(
            title=verse.title.title,
            content=content,
            url=f"/title/{verse.title_id}",
            type_name="بیت شعر"
        ))
    
    # تبدیل به دیکشنری برای JSON
    results_data = []
    for result in results:
        results_data.append({
            'title': result.title,
            'content': result.content,
            'url': result.url,
            'type': result.type_name
        })
    
    return jsonify({
        'results': results_data,
        'count': len(results_data),
        'query': query
    })

@main_bp.route('/api/gardens')
def api_gardens():
    """API برای دریافت لیست باغ‌ها"""
    
    gardens = []
    for garden_num in range(1, 5):
        title_count = Title.query.filter_by(garden=garden_num).count()
        garden_name = {
            1: 'خیابان اول باغ فردوس',
            2: 'خیابان دوم باغ فردوس',
            3: 'خیابان سوم باغ فردوس',
            4: 'خیابان چهارم باغ فردوس'
        }[garden_num]
        
        gardens.append({
            'id': garden_num,
            'name': garden_name,
            'title_count': title_count,
            'url': f'/garden/{garden_num}'
        })
    
    return jsonify({'gardens': gardens})

@main_bp.route('/api/titles/<int:garden_id>')
def api_titles(garden_id):
    """API برای دریافت عناوین یک باغ"""
    
    if garden_id < 1 or garden_id > 4:
        return jsonify({'error': 'باغ مورد نظر یافت نشد.'}), 404
    
    titles = Title.query.filter_by(garden=garden_id)\
                       .order_by(Title.order_in_garden)\
                       .all()
    
    titles_data = []
    for title in titles:
        verse_count = title.verses.count()
        titles_data.append({
            'id': title.id,
            'title': title.title,
            'verse_count': verse_count,
            'url': f'/title/{title.id}'
        })
    
    return jsonify({'titles': titles_data})

@main_bp.route('/about')
def about():
    """درباره سایت و شاعر"""
    return render_template('about.html')

@main_bp.errorhandler(404)
def not_found_error(error):
    """صفحه خطای ۴۰۴"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """صفحه خطای ۵۰۰"""
    db.session.rollback()
    return render_template('errors/500.html'), 500