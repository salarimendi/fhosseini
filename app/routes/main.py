#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مسیرهای اصلی پروژه فردوسی حسینی
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, Response, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import or_, func
from app.models import Title, Verse, Comment, Recording, User, SearchResult
from app.forms import CommentForm
from app import db
from datetime import datetime
from flask_mail import Message
from app import mail

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """صفحه اصلی - نمایش باغ‌ها"""
    
    # دریافت آمار کلی
    stats = {
        'total_poems': Title.query.count(),
        'total_verses': Verse.query.count(),
        'total_comments': Comment.query.filter_by(status='approved').count(),
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
    recent_comments = Comment.query.filter_by(status='approved')\
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
    comments = Comment.query.filter_by(title_id=title_id, status='approved').order_by(Comment.created_at.desc()).all()
    
    # بررسی اینکه آیا کاربر قبلاً نظر داده است
    user_has_comment = False
    if current_user.is_authenticated:
        user_has_comment = Comment.query.filter_by(
            user_id=current_user.id,
            title_id=title_id
        ).first() is not None
    
    # ایجاد فرم نظر
    comment_form = CommentForm() if current_user.is_authenticated and current_user.can_comment() else None
    
    # بررسی اینکه آیا کاربر ضبط دارد و وضعیت تأیید آن
    user_has_recording = False
    user_recording_approved = False
    if current_user.is_authenticated:
        user_recording = Recording.query.filter_by(
            user_id=current_user.id,
            title_id=title_id
        ).first()
        if user_recording:
            user_has_recording = True
            user_recording_approved = user_recording.is_approved
    
    # دریافت ضبط‌های صوتی
    recordings = []
    for recording in title_obj.recordings:
        # نمایش فایل‌های تأیید شده برای همه
        # نمایش فایل‌های تأیید نشده فقط برای ادمین‌ها
        if recording.is_approved or (current_user.is_authenticated and current_user.is_admin):
            # دریافت اطلاعات کاربر
            user = User.query.get(recording.user_id)
            recordings.append({
                'id': recording.id,
                'reader_name': user.fullname if user else recording.user.username,  # استفاده از نام کامل
                'filename': recording.filename,
                'file_path': recording.file_path,
                'file_size_mb': recording.file_size_mb,
                'duration': recording.duration,
                'created_at': recording.created_at,
                'is_approved': recording.is_approved,
                'user_id': recording.user_id
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
        'comment_count': len(comments),
        'recording_count': len(recordings)
    }
    # تعداد ابیات قبلی در کل کتاب (برای شماره سراسری)
    prev_verses_count = title_obj.preceding_verses_count()
    # تعداد کل ابیات (غیر زیرعنوان) در کل کتاب
    total_verses_all = Verse.query.filter_by(is_subtitle=0).count()

    return render_template('poem.html',
        title=title_obj,
        verses=verses,
        comments=comments,
        recordings=recordings,
        prev_title=prev_title,
        next_title=next_title,
        stats=poem_stats,
        user_has_comment=user_has_comment,
        comment_form=comment_form,
        user_has_recording=user_has_recording,
        user_recording_approved=user_recording_approved,
        prev_verses_count=prev_verses_count,
        total_verses_all=total_verses_all
    )

@main_bp.route('/search')
def search():
    """جستجو در عناوین و ابیات"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    results = []
    
    # جستجو در عناوین
    titles = Title.query.filter(Title.title.contains(query)).all()
    for title in titles:
        results.append({
            'type': 'title',
            'title_id': title.id,
            'title': title.title,
            'garden': title.garden,
            'verse_preview': None
        })
    
    # جستجو در ابیات
    verses = Verse.query.join(Title).filter(
        or_(
            Verse.verse_1.contains(query),
            Verse.verse_2.contains(query)
        )
    ).all()
    
    for verse in verses:
        # تعیین کدام مصرع شامل عبارت جستجو است
        verse_preview = verse.verse_1 if query.lower() in verse.verse_1.lower() else verse.verse_2
        
        results.append({
            'type': 'verse',
            'title_id': verse.title_id,
            'title': verse.title.title,
            'garden': verse.title.garden,
            'verse_preview': verse_preview
        })
    
    return jsonify(results)

@main_bp.route('/advanced_search')
def advanced_search():
    """صفحه جستجوی پیشرفته"""
    return render_template('advanced_search.html')

@main_bp.route('/random_poem')
def random_poem():
    """انتخاب تصادفی یک شعر"""
    random_title = Title.query.order_by(func.random()).first()
    if random_title:
        return redirect(url_for('main.title', title_id=random_title.id))
    return redirect(url_for('main.home'))

@main_bp.route('/api/gardens')
def api_gardens():
    """API برای دریافت لیست باغ‌ها"""
    gardens = []
    
    for garden_num in range(1, 5):
        garden_titles = Title.query.filter_by(garden=garden_num).count()
        sample_title = Title.query.filter_by(garden=garden_num).first()
        
        if sample_title:
            gardens.append({
                'number': garden_num,
                'name': sample_title.garden_name,
                'title_count': garden_titles
            })
    
    return jsonify({
        'gardens': gardens,
        'count': len(gardens)
    })

@main_bp.route('/api/titles/<int:garden_num>')
def api_titles(garden_num):
    """API برای دریافت عناوین یک باغ"""
    if garden_num < 1 or garden_num > 4:
        return jsonify({
            'error': 'شماره باغ نامعتبر است.',
            'titles': [],
            'count': 0
        }), 400
    
    titles = Title.query.filter_by(garden=garden_num)\
                       .order_by(Title.order_in_garden)\
                       .all()
    
    return jsonify({
        'titles': [{
            'id': title.id,
            'title': title.title,
            'order': title.order_in_garden,
            'verse_count': len(title.verses)
        } for title in titles],
        'count': len(titles)
    })

@main_bp.route('/api/title/<int:title_id>')
def api_title(title_id):
    """API برای دریافت جزئیات یک شعر"""
    title = Title.query.get_or_404(title_id)
    
    verses = []
    for verse in title.get_verses_ordered():
        verses.append({
            'id': verse.id,
            'text': verse.text,
            'text_fa': verse.text_fa,
            'order': verse.order_in_title
        })
    
    comments = []
    for comment in title.get_comments():
        if comment.is_approved:
            comments.append({
                'id': comment.id,
                'text': comment.text,
                'user': comment.user.username,
                'created_at': comment.created_at.isoformat()
            })
    
    recordings = []
    for recording in title.recordings.filter_by(is_approved=True):
        recordings.append({
            'id': recording.id,
            'reader': recording.user.username,
            'filename': recording.filename,
            'file_size': recording.file_size_mb,
            'duration': recording.duration,
            'created_at': recording.created_at.isoformat()
        })
    
    return jsonify({
        'id': title.id,
        'title': title.title,
        'garden': title.garden,
        'garden_name': title.garden_name,
        'order': title.order_in_garden,
        'verses': verses,
        'comments': comments,
        'recordings': recordings
    })

@main_bp.route('/statistics')
def statistics():
    """صفحه آمار کلی سایت"""
    
    # آمار کلی
    total_stats = {
        'poems': Title.query.count(),
        'verses': Verse.query.count(),
        'comments': Comment.query.filter_by(is_approved=True).count(),
        'recordings': Recording.query.filter_by(is_approved=True).count(),
        'users': User.query.filter_by(is_active=True).count()
    }
    
    # آمار هر باغ
    garden_stats = []
    for garden_num in range(1, 5):
        garden_titles = Title.query.filter_by(garden=garden_num).count()
        sample_title = Title.query.filter_by(garden=garden_num).first()
        garden_name = sample_title.garden_name if sample_title else f'باغ {garden_num}'
        
        garden_verses = db.session.query(func.count(Verse.id))\
                                 .join(Title)\
                                 .filter(Title.garden == garden_num)\
                                 .scalar()
        
        garden_comments = db.session.query(func.count(Comment.id))\
                                   .join(Title)\
                                   .filter(Title.garden == garden_num,
                                         Comment.is_approved == True)\
                                   .scalar()
        
        garden_recordings = db.session.query(func.count(Recording.id))\
                                     .join(Title)\
                                     .filter(Title.garden == garden_num,
                                           Recording.is_approved == True)\
                                     .scalar()
        
        garden_stats.append({
            'number': garden_num,
            'name': garden_name,
            'titles': garden_titles,
            'verses': garden_verses,
            'comments': garden_comments,
            'recordings': garden_recordings
        })
    
    return render_template('statistics.html',
                         total_stats=total_stats,
                         garden_stats=garden_stats)

@main_bp.route('/about')
def about():
    """صفحه درباره ما"""
    return render_template('about.html')

@main_bp.route('/articles')
def articles():
    """صفحه مقالات"""
    return render_template('articles.html')

@main_bp.route('/research-collaboration')
def research_collaboration():
    """صفحه فراخوان همکاری پژوهشی"""
    return render_template('research_collaboration.html')

@main_bp.route('/contact')
def contact():
    """صفحه تماس با ما"""
    return render_template('contact.html')

@main_bp.route('/send-message', methods=['POST'])
def send_message():
    """ارسال پیام از فرم تماس"""
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    # اعتبارسنجی فیلدها
    if not all([name, email, subject, message]):
        flash('لطفاً تمام فیلدها را پر کنید.', 'error')
        return redirect(url_for('main.contact'))
    
    try:
        msg = Message(
            subject=f'پیام جدید از {name}: {subject}',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_DEFAULT_SENDER']],  # ارسال به آدرس پیش‌فرض
            body=f'''پیام جدید از طریق فرم تماس:

نام و نام خانوادگی: {name}
ایمیل: {email}
موضوع: {subject}

متن پیام:
{message}
'''
        )
        mail.send(msg)
        flash('پیام شما با موفقیت ارسال شد.', 'success')
    except Exception as e:
        current_app.logger.error(f'خطا در ارسال ایمیل: {str(e)}')
        flash('خطا در ارسال پیام. لطفاً دوباره تلاش کنید.', 'error')
    
    return redirect(url_for('main.contact'))



@main_bp.route('/documentation')
def documentation_page():
    """صفحه مستندسازی و تطبیق تاریخی"""
    from app.models import Title, Comment
    from sqlalchemy import func
    
    total_titles = Title.query.count()
    documented_titles = Title.query.join(Title.comments).filter(Comment.status == 'approved').distinct().count()
    percent = int((documented_titles / total_titles) * 100) if total_titles else 0
    
    # اطلاعات تفصیلی هر باغ
    garden_details = []
    for garden_num in range(1, 5):
        garden_titles = Title.query.filter_by(garden=garden_num).order_by(Title.order_in_garden).all()
        
        garden_data = {
            'number': garden_num,
            'name': f'خیابان {garden_num} باغ فردوس',
            'titles': []
        }
        
        for title in garden_titles:
            # بررسی اینکه آیا این تیتر مستندسازی شده یا نه
            is_documented = Comment.query.filter_by(
                title_id=title.id, 
                status='approved'
            ).first() is not None
            
            garden_data['titles'].append({
                'id': title.id,
                'title': title.title,
                'order': title.order_in_garden,
                'is_documented': is_documented
            })
        
        garden_details.append(garden_data)
    
    return render_template('documentation.html', 
                         total_titles=total_titles, 
                         documented_titles=documented_titles, 
                         percent=percent,
                         garden_details=garden_details)

@main_bp.route('/textual-criticism')
def textual_criticism_page():
    """صفحه نسخه‌پژوهی"""
    return render_template('textual_criticism.html')

@main_bp.route('/biography')
def biography_page():
    """صفحه زندگینامه الهامی"""
    return render_template('biography.html')

@main_bp.route('/ilhami-manuscript-studies')
def ilhami_manuscript_studies():
    """صفحه نسخه شناسی الهامی"""
    return render_template('ilhami_manuscript_studies.html')


# -----------------------------
# SEO: robots.txt و sitemap.xml
# -----------------------------
@main_bp.route('/robots.txt')
def robots_txt():
    """ارائه robots.txt از فایل استاتیک"""
    return send_from_directory('static', 'robots.txt')


@main_bp.route('/sitemap.xml')
def sitemap_xml():
    """ارائه sitemap.xml از فایل استاتیک"""
    return send_from_directory('static', 'sitemap.xml')

@main_bp.errorhandler(404)
def not_found_error(error):
    """صفحه خطای ۴۰۴"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """صفحه خطای ۵۰۰"""
    db.session.rollback()
    return render_template('errors/500.html'), 500