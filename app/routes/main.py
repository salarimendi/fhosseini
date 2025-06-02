#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای اصلی پروژه فردوسی حسینی
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import or_, func
from app.models import Title, Verse, Comment, Recording, User, SearchResult
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """صفحه اصلی - نمایش باغ‌ها"""
    
    # دریافت آمار کلی
    stats = {
        'total_poems': Title.query.count(),
        'total_verses': Verse.query.count(),
        'total_comments': Comment.query.filter_by(is_approved=True).count(),
        'total_recordings': Recording.query.filter_by(is_approved=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'gardens': []
    }
    
    # آمار هر باغ
    for garden_num in range(1, 5):
        garden_titles = Title.query.filter_by(garden=garden_num).count()
        
        # استفاده از property garden_name از مدل
        sample_title = Title.query.filter_by(garden=garden_num).first()
        garden_name = sample_title.garden_name if sample_title else f'باغ {garden_num}'
        
        # آمار ابیات این باغ
        garden_verses = db.session.query(func.count(Verse.id))\
                                 .join(Title)\
                                 .filter(Title.garden == garden_num)\
                                 .scalar()
        
        stats['gardens'].append({
            'number': garden_num,
            'name': garden_name,
            'title_count': garden_titles,
            'verse_count': garden_verses
        })
    
    # آخرین نظرات تأیید شده
    recent_comments = Comment.query.filter_by(is_approved=True)\
                                  .order_by(Comment.created_at.desc())\
                                  .limit(5).all()
    
    # آخرین ضبط‌های تأیید شده
    recent_recordings = Recording.query.filter_by(is_approved=True)\
                                      .order_by(Recording.created_at.desc())\
                                      .limit(5).all()
    
    return render_template('home.html', 
                         stats=stats,
                         recent_comments=recent_comments,
                         recent_recordings=recent_recordings)

@main_bp.route('/garden/<int:garden_num>')
def garden(garden_num):
    """نمایش عناوین یک باغ خاص"""
    
    if garden_num < 1 or garden_num > 4:
        flash('باغ مورد نظر یافت نشد.', 'error')
        return redirect(url_for('main.home'))
    
    # دریافت عناوین باغ مرتب شده
    titles = Title.query.filter_by(garden=garden_num)\
                       .order_by(Title.order_in_garden)\
                       .all()
    
    if not titles:
        flash(f'هیچ شعری در این باغ یافت نشد.', 'info')
        return redirect(url_for('main.home'))
    
    # استفاده از property garden_name از مدل
    garden_name = titles[0].garden_name
    
    # آمار باغ
    garden_stats = {
        'title_count': len(titles),
        'verse_count': db.session.query(func.count(Verse.id))\
                                .join(Title)\
                                .filter(Title.garden == garden_num)\
                                .scalar(),
        'comment_count': db.session.query(func.count(Comment.id))\
                                  .join(Title)\
                                  .filter(Title.garden == garden_num, Comment.is_approved == True)\
                                  .scalar(),
        'recording_count': db.session.query(func.count(Recording.id))\
                                    .join(Title)\
                                    .filter(Title.garden == garden_num, Recording.is_approved == True)\
                                    .scalar()
    }
    
    return render_template('garden.html', 
                         titles=titles, 
                         garden_num=garden_num,
                         garden_name=garden_name,
                         garden_stats=garden_stats)

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
    for recording in title_obj.recordings.filter_by(is_approved=True):
        recordings.append({
            'id': recording.id,
            'reader_name': recording.user.username,
            'filename': recording.filename,
            'file_path': recording.file_path,
            'file_size_mb': recording.file_size_mb,
            'duration': recording.duration,
            'created_at': recording.created_at
        })
    
    # شعر قبلی و بعدی در همان باغ
    prev_title = Title.query.filter(
        Title.garden == title_obj.garden,
        Title.order_in_garden < title_obj.order_in_garden
    ).order_by(Title.order_in_garden.desc()).first()
    
    next_title = Title.query.filter(
        Title.garden == title_obj.garden,
        Title.order_in_garden > title_obj.order_in_garden
    ).order_by(Title.order_in_garden.asc()).first()
    
    # آمار شعر
    poem_stats = {
        'verse_count': len(verses),
        'comment_count': len(approved_comments),
        'recording_count': len(recordings)
    }
    
    return render_template('poem.html',
                         title=title_obj,
                         verses=verses,
                         comments=approved_comments,
                         recordings=recordings,
                         prev_title=prev_title,
                         next_title=next_title,
                         poem_stats=poem_stats)


@main_bp.route('/search')
def search():
    """جستجو در عناوین و ابیات"""
    
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, title, verse
    garden = request.args.get('garden', '')
    
    if not query:
        return jsonify({'results': [], 'message': 'لطفاً کلمه کلیدی وارد کنید.'})
    
    results = []
    
    # فیلتر باغ
    garden_filter = None
    if garden and garden.isdigit():
        garden_num = int(garden)
        if 1 <= garden_num <= 4:
            garden_filter = garden_num
    
    # جستجو در عناوین
    if search_type in ['all', 'title']:
        title_query = Title.query.filter(Title.title.contains(query))
        if garden_filter:
            title_query = title_query.filter(Title.garden == garden_filter)
        
        title_results = title_query.all()
        
        for title in title_results:
            results.append(SearchResult(
                title=title.title,
                content=f"از {title.garden_name}",
                url=f"/title/{title.id}",
                type_name="عنوان شعر"
            ))
    
    # جستجو در ابیات
    if search_type in ['all', 'verse']:
        verse_query = Verse.query.filter(
            or_(Verse.verse_1.contains(query), 
                Verse.verse_2.contains(query))
        )
        
        if garden_filter:
            verse_query = verse_query.join(Title).filter(Title.garden == garden_filter)
        
        verse_results = verse_query.limit(20).all()
        
        for verse in verse_results:
            # نمایش بیت حاوی کلمه جستجو
            content = verse.verse_1
            if verse.verse_2 and query.lower() in verse.verse_2.lower():
                content = verse.verse_2
            
            # هایلایت کلمه جستجو
            highlighted_content = content.replace(query, f'<mark>{query}</mark>')
            
            results.append(SearchResult(
                title=verse.title.title,
                content=highlighted_content,
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
        'query': query,
        'search_type': search_type,
        'garden': garden_filter
    })

@main_bp.route('/advanced_search')
def advanced_search():
    """صفحه جستجوی پیشرفته"""
    return render_template('search/advanced.html')

@main_bp.route('/random_poem')
def random_poem():
    """نمایش شعر تصادفی"""
    
    # انتخاب شعر تصادفی
    title_obj = Title.query.order_by(func.random()).first()
    
    if not title_obj:
        flash('هیچ شعری یافت نشد.', 'error')
        return redirect(url_for('main.home'))
    
    return redirect(url_for('main.title', title_id=title_obj.id))

@main_bp.route('/api/gardens')
def api_gardens():
    """API برای دریافت لیست باغ‌ها"""
    
    gardens = []
    for garden_num in range(1, 5):
        title_count = Title.query.filter_by(garden=garden_num).count()
        
        # استفاده از property garden_name
        sample_title = Title.query.filter_by(garden=garden_num).first()
        garden_name = sample_title.garden_name if sample_title else f'باغ {garden_num}'
        
        gardens.append({
            'id': garden_num,
            'name': garden_name,
            'title_count': title_count,
            'url': f'/garden/{garden_num}'
        })
    
    return jsonify({'gardens': gardens})

@main_bp.route('/api/titles/<int:garden_num>')
def api_titles(garden_num):
    """API برای دریافت عناوین یک باغ"""
    
    if garden_num < 1 or garden_num > 4:
        return jsonify({'error': 'باغ مورد نظر یافت نشد.'}), 404
    
    titles = Title.query.filter_by(garden=garden_num)\
                       .order_by(Title.order_in_garden)\
                       .all()
    
    titles_data = []
    for title in titles:
        verse_count = title.verses.count()
        comment_count = title.comments.filter_by(is_approved=True).count()
        recording_count = title.recordings.filter_by(is_approved=True).count()
        
        titles_data.append({
            'id': title.id,
            'title': title.title,
            'verse_count': verse_count,
            'comment_count': comment_count,
            'recording_count': recording_count,
            'url': f'/title/{title.id}'
        })
    
    return jsonify({'titles': titles_data})

@main_bp.route('/api/title/<int:title_id>')
def api_title(title_id):
    """API برای دریافت اطلاعات یک شعر"""
    
    title_obj = Title.query.get_or_404(title_id)
    
    verses_data = []
    for verse in title_obj.get_verses_ordered():
        verses_data.append({
            'id': verse.id,
            'order': verse.order_in_title,
            'verse_1': verse.verse_1,
            'verse_2': verse.verse_2,
            'full_verse': verse.full_verse
        })
    
    comments_data = []
    for comment in title_obj.get_comments():
        if comment.is_approved:
            comments_data.append({
                'id': comment.id,
                'author': comment.author.username,
                'comment': comment.comment,
                'created_at': comment.created_at.isoformat()
            })
    
    recordings_data = []
    for recording in title_obj.recordings.filter_by(is_approved=True):
        recordings_data.append({
            'id': recording.id,
            'reader': recording.user.username,
            'filename': recording.filename,
            'file_path': recording.file_path,
            'duration': recording.duration,
            'file_size_mb': recording.file_size_mb
        })
    
    return jsonify({
        'id': title_obj.id,
        'title': title_obj.title,
        'garden': title_obj.garden,
        'garden_name': title_obj.garden_name,
        'order_in_garden': title_obj.order_in_garden,
        'verses': verses_data,
        'comments': comments_data,
        'recordings': recordings_data
    })

@main_bp.route('/statistics')
def statistics():
    """صفحه آمار کلی سایت"""
    
    # آمار کلی
    general_stats = {
        'total_poems': Title.query.count(),
        'total_verses': Verse.query.count(),
        'total_comments': Comment.query.filter_by(is_approved=True).count(),
        'total_recordings': Recording.query.filter_by(is_approved=True).count(),
        'total_users': User.query.filter_by(is_active=True).count(),
        'researchers': User.query.filter_by(role='researcher', is_active=True).count(),
        'readers': User.query.filter_by(role='reader', is_active=True).count()
    }
    
    # آمار باغ‌ها
    garden_stats = []
    for garden_num in range(1, 5):
        sample_title = Title.query.filter_by(garden=garden_num).first()
        garden_name = sample_title.garden_name if sample_title else f'باغ {garden_num}'
        
        stats = {
            'number': garden_num,
            'name': garden_name,
            'title_count': Title.query.filter_by(garden=garden_num).count(),
            'verse_count': db.session.query(func.count(Verse.id))\
                                    .join(Title)\
                                    .filter(Title.garden == garden_num)\
                                    .scalar(),
            'comment_count': db.session.query(func.count(Comment.id))\
                                      .join(Title)\
                                      .filter(Title.garden == garden_num, Comment.is_approved == True)\
                                      .scalar(),
            'recording_count': db.session.query(func.count(Recording.id))\
                                        .join(Title)\
                                        .filter(Title.garden == garden_num, Recording.is_approved == True)\
                                        .scalar()
        }
        garden_stats.append(stats)
    
    return render_template('statistics.html',
                         general_stats=general_stats,
                         garden_stats=garden_stats)

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