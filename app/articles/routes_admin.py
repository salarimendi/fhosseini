# -*- coding: utf-8 -*-
"""
app/articles/routes_admin.py

مدیریت مقالات برای کاربران با نقش admin یا researcher (محقق) - کاملاً
مجزا از app/routes/admin.py موجود پروژه (آن فایل اصلاً لمس نمی‌شود).
"""

import os
import uuid
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, jsonify, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.articles.models import Article, ArticleCategory
from app.articles.forms import ArticleForm, ArticleCategoryForm
from app.articles.utils import unique_slug, sanitize_html, html_to_excerpt

admin_bp = Blueprint(
    'articles_admin',
    __name__,
    url_prefix='/admin/articles',
    template_folder='templates',  # -> app/articles/templates (namespaced articles/admin/*.html)
)

# نقش‌های مجاز برای مدیریت مقاله - اگر نام نقش «محقق» در پروژه‌ی شما چیز
# دیگری است (مثلاً 'researcher' با حروف/نام دیگر)، همین‌جا اصلاح کنید.
ALLOWED_ROLES = ('admin', 'researcher')


def article_editor_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, 'role', None) not in ALLOWED_ROLES:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# کمکی: ذخیره‌ی فایل تصویر آپلودشده
# ---------------------------------------------------------------------------
def _allowed_image(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config.get(
        'ARTICLE_IMAGE_ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    )


def save_uploaded_image(file_storage):
    """
    فایل را در ARTICLE_IMAGE_UPLOAD_FOLDER (پیش‌فرض: uploads/articles_images/)
    ذخیره می‌کند و فقط نام یکتای فایل را برمی‌گرداند (نه کل URL).
    """
    if not file_storage or not file_storage.filename:
        return None

    if not _allowed_image(file_storage.filename):
        raise ValueError('فرمت تصویر مجاز نیست.')

    max_size_mb = current_app.config.get('ARTICLE_IMAGE_MAX_SIZE_MB', 5)
    file_storage.stream.seek(0, os.SEEK_END)
    size_mb = file_storage.stream.tell() / (1024 * 1024)
    file_storage.stream.seek(0)
    if size_mb > max_size_mb:
        raise ValueError(f'حجم تصویر نباید بیشتر از {max_size_mb} مگابایت باشد.')

    ext = secure_filename(file_storage.filename).rsplit('.', 1)[-1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'

    upload_folder = current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file_storage.save(os.path.join(upload_folder, unique_name))

    return unique_name


def image_url(filename):
    """ساخت URL نهایی تصویر از روی نام فایل ذخیره‌شده."""
    if not filename:
        return None
    return url_for('articles_public.media', filename=filename)


# ---------------------------------------------------------------------------
# لیست مقالات (پنل مدیریت مقالات)
# ---------------------------------------------------------------------------
@admin_bp.route('/')
@article_editor_required
def list_articles():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')

    query = Article.query.order_by(Article.created_at.desc())
    if status_filter in ('draft', 'published'):
        query = query.filter_by(status=status_filter)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'articles/admin/list.html',
        articles=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        image_url=image_url,
        pending_corrections_count = 0
    )



# ---------------------------------------------------------------------------
# ساخت مقاله‌ی جدید
# ---------------------------------------------------------------------------
@admin_bp.route('/new', methods=['GET', 'POST'])
@article_editor_required
def new_article():

    form = ArticleForm()
    form.category_id.choices = [(0, '— بدون دسته‌بندی —')] + [
        (c.id, c.name) for c in ArticleCategory.query.order_by(ArticleCategory.name).all()
    ]


    if form.validate_on_submit():
        content = sanitize_html(form.content_html.data)

        article = Article(
            title=form.title.data.strip(),
            slug=unique_slug(form.title.data, Article),
            content_html=content,
            excerpt=(form.excerpt.data or html_to_excerpt(content)),
            meta_title=form.meta_title.data or None,
            meta_description=form.meta_description.data or None,
            meta_keywords=form.meta_keywords.data or None,
            status=form.status.data,
            category_id=(form.category_id.data or None),
            author_id=current_user.id,
        )

        if form.featured_image.data:
            try:
                article.featured_image_filename = save_uploaded_image(form.featured_image.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('articles/admin/editor.html', form=form, article=None, image_url=image_url,
                                       pending_corrections_count =0)

        if article.status == Article.STATUS_PUBLISHED:
            article.publish()

        db.session.add(article)
        db.session.commit()
        flash('مقاله با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('articles_admin.list_articles'))

    return render_template('articles/admin/editor.html', form=form, article=None, image_url=image_url,
                           pending_corrections_count =0)


# ---------------------------------------------------------------------------
# ویرایش مقاله
# ---------------------------------------------------------------------------
@admin_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@article_editor_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    form = ArticleForm(obj=article)
    form.category_id.choices = [(0, '— بدون دسته‌بندی —')] + [
        (c.id, c.name) for c in ArticleCategory.query.order_by(ArticleCategory.name).all()
    ]

    if request.method == 'GET':
        form.category_id.data = article.category_id or 0

    if form.validate_on_submit():
        content = sanitize_html(form.content_html.data)
        was_published = article.is_published

        new_title = form.title.data.strip()
        if new_title != article.title:
            article.slug = unique_slug(new_title, Article, instance_id=article.id)
        article.title = new_title

        article.content_html = content
        article.excerpt = form.excerpt.data or html_to_excerpt(content)
        article.meta_title = form.meta_title.data or None
        article.meta_description = form.meta_description.data or None
        article.meta_keywords = form.meta_keywords.data or None
        article.status = form.status.data
        article.category_id = form.category_id.data or None

        if form.featured_image.data:
            try:
                article.featured_image_filename = save_uploaded_image(form.featured_image.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('articles/admin/editor.html', form=form, article=article, image_url=image_url)

        if not was_published and article.is_published:
            article.publish()

        db.session.commit()
        flash('تغییرات ذخیره شد.', 'success')
        return redirect(url_for('articles_admin.list_articles'))

    return render_template('articles/admin/editor.html', form=form, article=article, image_url=image_url)


# ---------------------------------------------------------------------------
# حذف مقاله
# ---------------------------------------------------------------------------
@admin_bp.route('/<int:article_id>/delete', methods=['POST'])
@article_editor_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('مقاله حذف شد.', 'info')
    return redirect(url_for('articles_admin.list_articles'))


# ---------------------------------------------------------------------------
# مدیریت دسته‌بندی‌ها
# ---------------------------------------------------------------------------
@admin_bp.route('/categories', methods=['GET', 'POST'])
@article_editor_required
def categories():
    form = ArticleCategoryForm()
    if form.validate_on_submit():
        category = ArticleCategory(
            name=form.name.data.strip(),
            slug=unique_slug(form.name.data, ArticleCategory),
            description=form.description.data,
        )
        db.session.add(category)
        db.session.commit()
        flash('دسته‌بندی اضافه شد.', 'success')
        return redirect(url_for('articles_admin.categories'))

    all_categories = ArticleCategory.query.order_by(ArticleCategory.name).all()
    return render_template('articles/admin/categories.html', form=form, categories=all_categories,
                           pending_corrections_count =0)


# ---------------------------------------------------------------------------
# آپلود تصویر داخل متن برای TinyMCE - پاسخ JSON با فیلد "location"
# ---------------------------------------------------------------------------
@admin_bp.route('/upload-image', methods=['POST'])
@article_editor_required
def upload_image():
    file_storage = request.files.get('file')
    try:
        filename = save_uploaded_image(file_storage)
        if not filename:
            return jsonify({'error': 'فایلی ارسال نشده است.'}), 400
        return jsonify({'location': image_url(filename)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
