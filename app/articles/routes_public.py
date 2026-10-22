# -*- coding: utf-8 -*-
"""
app/articles/routes_public.py

بلوپرینت عمومی نمایش مقالات - کاملاً مجزا از app/routes/main.py.
این بلوپرینت همچنین صاحب پوشه‌ی static اختصاصی ماژول (app/articles/static)
و مسیر سرو کردن تصاویر آپلودشده (uploads/articles_images) است، تا هیچ
فایلی از app/static اصلی یا app/routes/main.py لازم نباشد لمس شود.
"""

import os
from flask import (
    Blueprint, render_template, abort, request, current_app, send_from_directory
)

from flask import redirect, url_for

from app import db, limiter
from app.articles.models import Article, ArticleCategory, SECTION_ARTICLES, SECTION_ACTIVITIES
from urllib.parse import unquote
from unicodedata import normalize


public_bp = Blueprint(
    'articles_public',
    __name__,
    url_prefix='/articles',
    template_folder='templates',   # -> app/articles/templates (namespaced articles/public/*.html)
    static_folder='static',        # -> app/articles/static
    static_url_path='/articles/assets',
)


@public_bp.route('/media/<path:filename>')
@limiter.exempt
def media(filename):
    """
    سرو کردن تصاویر آپلودشده‌ی مقالات از پوشه‌ی سطح‌بالای uploads/articles_images
    (هم‌راستا با الگوی موجود پروژه برای uploads/research_images).
    این یک route جدا و مستقل است - به هیچ مکانیزم serve دیگری در پروژه نیاز ندارد.
    """
    upload_folder = current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@public_bp.route('/')
def list_articles():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ARTICLES_PER_PAGE', 10)

    query = Article.query.filter_by(status=Article.STATUS_PUBLISHED, section=SECTION_ARTICLES).order_by(
        Article.published_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = ArticleCategory.query.filter_by(section=SECTION_ARTICLES).order_by(ArticleCategory.name).all()

    return render_template(
        'articles/public/list.html',
        articles=pagination.items,
        pagination=pagination,
        categories=categories,
    )


@public_bp.route('/category/<slug>')
def by_category(slug):
    slug = normalize('NFC', unquote(slug))
    category = ArticleCategory.query.filter_by(slug=slug).first_or_404()
    if category.section == SECTION_ACTIVITIES:
        return redirect(url_for('activities_public.by_category', slug=category.slug))
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ARTICLES_PER_PAGE', 10)

    query = category.articles.filter_by(status=Article.STATUS_PUBLISHED).order_by(
        Article.published_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = ArticleCategory.query.filter_by(section=SECTION_ARTICLES).order_by(ArticleCategory.name).all()

    return render_template(
        'articles/public/list.html',
        articles=pagination.items,
        pagination=pagination,
        categories=categories,
        active_category=category,
    )


@public_bp.route('/<slug>')
def detail(slug):
    slug = normalize('NFC', unquote(slug))  # برای اطمینان از تطابق با slugهای یونیکد    
    article = Article.query.filter_by(slug=slug).first_or_404()

    if not article.is_published:
        abort(404)
    if article.section == SECTION_ACTIVITIES:
        return redirect(url_for('activities_public.detail', slug=article.slug))

    article.views = (article.views or 0) + 1
    db.session.commit()

    related = (
        Article.query.filter_by(status=Article.STATUS_PUBLISHED, category_id=article.category_id)
        .filter(Article.id != article.id)
        .order_by(Article.published_at.desc())
        .limit(4)
        .all()
        if article.category_id
        else []
    )

    return render_template('articles/public/detail.html', article=article, related=related)


# ===========================================================================
# وبلاگ فعالیت‌ها — همان مدل Article با section='activities'
# (ایجاد/ویرایش در همان پنل مدیریت مقالات: /admin/articles/new?section=activities)
# ===========================================================================
activities_bp = Blueprint(
    'activities_public',
    __name__,
    url_prefix='/activities',
    template_folder='templates',
)


def _activities_query():
    return Article.query.filter_by(status=Article.STATUS_PUBLISHED, section=SECTION_ACTIVITIES)


def _activity_categories():
    return ArticleCategory.query.filter_by(section=SECTION_ACTIVITIES).order_by(ArticleCategory.name).all()


@activities_bp.route('/')
def list_activities():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ACTIVITIES_PER_PAGE', 6)
    pagination = _activities_query().order_by(Article.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template(
        'articles/public/activities_list.html',
        activities=pagination.items,
        pagination=pagination,
        categories=_activity_categories(),
    )


@activities_bp.route('/category/<slug>')
def by_category(slug):
    slug = normalize('NFC', unquote(slug))
    category = ArticleCategory.query.filter_by(slug=slug).first_or_404()
    if category.section != SECTION_ACTIVITIES:
        return redirect(url_for('articles_public.by_category', slug=category.slug))
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ACTIVITIES_PER_PAGE', 6)
    pagination = _activities_query().filter_by(category_id=category.id).order_by(
        Article.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'articles/public/activities_list.html',
        activities=pagination.items,
        pagination=pagination,
        categories=_activity_categories(),
        active_category=category,
    )


@activities_bp.route('/<slug>')
def detail(slug):
    slug = normalize('NFC', unquote(slug))
    activity = Article.query.filter_by(slug=slug, section=SECTION_ACTIVITIES).first_or_404()
    if not activity.is_published:
        abort(404)

    activity.views = (activity.views or 0) + 1
    db.session.commit()

    # ناوبری مرحله‌ای: قدیمی‌تر ← جدیدتر (بر اساس زمان انتشار)
    older = (_activities_query().filter(Article.published_at < activity.published_at)
             .order_by(Article.published_at.desc()).first()) if activity.published_at else None
    newer = (_activities_query().filter(Article.published_at > activity.published_at)
             .order_by(Article.published_at.asc()).first()) if activity.published_at else None

    return render_template('articles/public/activity_detail.html', activity=activity,
                           older=older, newer=newer)
