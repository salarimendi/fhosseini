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
from app.utils.images import save_upload as save_image
from app.articles.models import SECTIONS, SECTION_ARTICLES, SECTION_ACTIVITIES
from app.articles.models import Article, ArticleCategory, ArticleMedia
from app.articles.forms import ArticleForm, ArticleCategoryForm
from app.articles.utils import (
    unique_slug, sanitize_html, html_to_excerpt, extract_media_filenames,
    remove_media_file,
)

admin_bp = Blueprint(
    'articles_admin',
    __name__,
    url_prefix='/admin/articles',
    template_folder='templates',  # -> app/articles/templates (namespaced articles/admin/*.html)
)

# نقش‌های مجاز برای مدیریت مقاله - اگر نام نقش «محقق» در پروژه‌ی شما چیز
# دیگری است (مثلاً 'researcher' با حروف/نام دیگر)، همین‌جا اصلاح کنید.
ALLOWED_ROLES = ('admin', 'researcher')

ADMIN_ONLY_ROLES = ('admin',)

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, 'role', None) not in ADMIN_ONLY_ROLES:
            abort(403)
        return view(*args, **kwargs)
    return wrapped



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
    upload_folder = current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
    # تبدیل به WebP (یا ذخیره‌ی عین فایل اگر IMAGE_WEBP_ON_UPLOAD=false)؛ فایل نامعتبر → ValueError
    saved = save_image(
        file_storage, upload_folder, uuid.uuid4().hex, ext,
        convert=current_app.config.get('IMAGE_WEBP_ON_UPLOAD', True),
        quality=current_app.config.get('IMAGE_WEBP_QUALITY', 82),
        max_side=current_app.config.get('IMAGE_MAX_SIDE', 2560))
    unique_name = saved.filename

    # متادیتای فایل در دیتابیس ثبت می‌شود؛ خود فایل فقط در uploads می‌ماند.
    db.session.add(ArticleMedia(
        filename=unique_name,
        original_name=secure_filename(file_storage.filename)[:255],
        mime_type=saved.mime,
        size_bytes=saved.size,
        uploaded_by=getattr(current_user, 'id', None),
    ))

    return unique_name


def _still_referenced(filename, exclude_id=None):
    """آیا مقاله‌ی دیگری هنوز از این فایل استفاده می‌کند؟"""
    q = Article.query.filter(
        db.or_(
            Article.featured_image_filename == filename,
            Article.content_html.like(f'%/articles/media/{filename}%'),
        )
    )
    if exclude_id is not None:
        q = q.filter(Article.id != exclude_id)
    return q.first() is not None


def _sync_media(article):
    """رکوردهای ArticleMedia را با فایل‌های واقعاً استفاده‌شده در مقاله هماهنگ می‌کند."""
    upload_folder = current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
    names = extract_media_filenames(article.content_html)
    if article.featured_image_filename:
        names.add(article.featured_image_filename)
    for name in names:
        row = ArticleMedia.query.filter_by(filename=name).first()
        if row is None:
            path = os.path.join(upload_folder, name)
            if not os.path.isfile(path):
                continue
            row = ArticleMedia(filename=name, size_bytes=os.path.getsize(path))
            db.session.add(row)
        if row.article_id is None:
            row.article_id = article.id


def _remove_if_unused(names, exclude_id=None):
    """فایل و رکورد مدیایی را که دیگر هیچ مقاله‌ای به آن ارجاع نمی‌دهد حذف می‌کند."""
    upload_folder = current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
    for name in names:
        if _still_referenced(name, exclude_id):
            continue
        ArticleMedia.query.filter_by(filename=name).delete()
        remove_media_file(upload_folder, name)


def image_url(filename):
    """ساخت URL نهایی تصویر از روی نام فایل ذخیره‌شده."""
    if not filename:
        return None
    return url_for('articles_public.media', filename=filename)


# ---------------------------------------------------------------------------
# لیست مقالات (پنل مدیریت مقالات)
# ---------------------------------------------------------------------------
def _section():
    """بخش جاری پنل: «مقالات» (پیش‌فرض) یا «وبلاگ فعالیت‌ها» — از ?section=activities."""
    value = request.args.get('section')
    return value if value in SECTIONS else SECTION_ARTICLES


def _category_choices(section):
    return [(0, '— بدون دسته‌بندی —')] + [
        (c.id, c.name)
        for c in ArticleCategory.query.filter_by(section=section).order_by(ArticleCategory.name).all()
    ]


def _after_save_url(article):
    if article.section == SECTION_ACTIVITIES:
        return url_for('activities_public.list_activities')
    return url_for('articles_public.list_articles')


def _apply_activity_fields(article, form):
    """فیلدهای مخصوص وبلاگ فعالیت‌ها (برای مقالات معمولی خالی می‌مانند)."""
    if article.section == SECTION_ACTIVITIES:
        article.stage_label = (form.stage_label.data or '').strip() or None
        article.contributors = (form.contributors.data or '').strip() or None
        article.video_url = (form.video_url.data or '').strip() or None


@admin_bp.route('/')
@admin_required
def list_articles():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')

    section = _section()
    query = Article.query.filter_by(section=section).order_by(Article.created_at.desc())
    if status_filter in ('draft', 'published'):
        query = query.filter_by(status=status_filter)

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'articles/admin/list.html',
        articles=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        section=section,
        image_url=image_url,
        pending_corrections_count = 0
    )



# ---------------------------------------------------------------------------
# ساخت مقاله‌ی جدید
# ---------------------------------------------------------------------------
@admin_bp.route('/new', methods=['GET', 'POST'])
@article_editor_required
def new_article():
    section = _section()
    form = ArticleForm()
    form.category_id.choices = _category_choices(section)


    if form.validate_on_submit():
        content = sanitize_html(form.content_html.data, current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'])

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
            section=section,
        )
        _apply_activity_fields(article, form)

        if form.featured_image.data:
            try:
                article.featured_image_filename = save_uploaded_image(form.featured_image.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('articles/admin/editor.html', form=form, article=None, section=section, image_url=image_url,
                                       pending_corrections_count =0)

        if article.status == Article.STATUS_PUBLISHED:
            article.publish()

        db.session.add(article)
        db.session.flush()
        _sync_media(article)
        db.session.commit()
        flash('مطلب با موفقیت ذخیره شد.', 'success')
        return redirect(_after_save_url(article))

    return render_template('articles/admin/editor.html', form=form, article=None, section=section, image_url=image_url,
                           pending_corrections_count =0)


# ---------------------------------------------------------------------------
# ویرایش مقاله
# ---------------------------------------------------------------------------
@admin_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
@article_editor_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user.role != 'admin' and article.author_id != current_user.id:
        abort(403)
    section = article.section
    form = ArticleForm(obj=article)
    form.category_id.choices = _category_choices(section)

    if request.method == 'GET':
        form.category_id.data = article.category_id or 0

    if form.validate_on_submit():
        content = sanitize_html(form.content_html.data, current_app.config['ARTICLE_IMAGE_UPLOAD_FOLDER'])
        was_published = article.is_published
        old_featured = article.featured_image_filename
        old_inline = extract_media_filenames(article.content_html)

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
        _apply_activity_fields(article, form)

        if form.featured_image.data:
            try:
                article.featured_image_filename = save_uploaded_image(form.featured_image.data)
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('articles/admin/editor.html', form=form, article=article, section=section, image_url=image_url,
                                       pending_corrections_count=0)

        if not was_published and article.is_published:
            article.publish()

        _sync_media(article)
        db.session.commit()

        # پاکسازی فایل‌های یتیم (تصویر شاخص جایگزین‌شده / تصاویر حذف‌شده از متن)
        still_used = extract_media_filenames(content)
        if article.featured_image_filename:
            still_used.add(article.featured_image_filename)
        stale = set(old_inline)
        if old_featured:
            stale.add(old_featured)
        stale -= still_used
        _remove_if_unused(stale, article.id)
        db.session.commit()

        flash('تغییرات ذخیره شد.', 'success')
        return redirect(_after_save_url(article))

    return render_template('articles/admin/editor.html', form=form, article=article, section=section, image_url=image_url,
                           pending_corrections_count=0)


# ---------------------------------------------------------------------------
# حذف مقاله
# ---------------------------------------------------------------------------
@admin_bp.route('/<int:article_id>/delete', methods=['POST'])
@admin_required
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    section = article.section
    files = extract_media_filenames(article.content_html)
    if article.featured_image_filename:
        files.add(article.featured_image_filename)
    files |= {m.filename for m in article.media}
    ArticleMedia.query.filter_by(article_id=article.id).delete()
    db.session.delete(article)
    db.session.flush()
    _remove_if_unused(files)
    db.session.commit()
    flash('مقاله حذف شد.', 'info')
    return redirect(url_for('articles_admin.list_articles', section=section))


# ---------------------------------------------------------------------------
# مدیریت دسته‌بندی‌ها
# ---------------------------------------------------------------------------
def _slug_taken(slug, instance_id=None):
    query = ArticleCategory.query.filter(ArticleCategory.slug == slug)
    if instance_id is not None:
        query = query.filter(ArticleCategory.id != instance_id)
    return query.first() is not None


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    section = _section()
    form = ArticleCategoryForm()
    if form.validate_on_submit():
        slug = form.slug.data or None
        if slug and _slug_taken(slug):
            form.slug.errors.append('این نشانی قبلاً برای دسته‌بندی دیگری استفاده شده است.')
        else:
            category = ArticleCategory(
                name=form.name.data.strip(),
                slug=slug or unique_slug(form.name.data, ArticleCategory),
                description=form.description.data,
                section=section,
            )
            db.session.add(category)
            db.session.commit()
            flash('دسته‌بندی اضافه شد.', 'success')
            return redirect(url_for('articles_admin.categories', section=section))

    all_categories = ArticleCategory.query.filter_by(section=section).order_by(ArticleCategory.name).all()
    return render_template('articles/admin/categories.html', form=form, categories=all_categories, section=section,
                           pending_corrections_count =0)


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = ArticleCategory.query.get_or_404(category_id)
    form = ArticleCategoryForm(obj=category)

    if form.validate_on_submit():
        # تغییر نام هرگز slug (و لینک‌های موجود) را عوض نمی‌کند؛ slug فقط با فیلد خودش تغییر می‌کند
        new_slug = form.slug.data or category.slug
        if new_slug != category.slug and _slug_taken(new_slug, category.id):
            form.slug.errors.append('این نشانی قبلاً برای دسته‌بندی دیگری استفاده شده است.')
        else:
            category.name = form.name.data.strip()
            category.slug = new_slug
            category.description = form.description.data
            db.session.commit()
            flash('دسته‌بندی ویرایش شد.', 'success')
            return redirect(url_for('articles_admin.categories', section=category.section))

    return render_template(
        'articles/admin/categories.html',
        form=form,
        categories=ArticleCategory.query.filter_by(section=category.section).order_by(ArticleCategory.name).all(),
        section=category.section,
        editing_category=category,
        pending_corrections_count=0,
    )


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = ArticleCategory.query.get_or_404(category_id)
    section = category.section
    Article.query.filter_by(category_id=category.id).update({Article.category_id: None})
    db.session.delete(category)
    db.session.commit()
    flash('دسته‌بندی حذف شد و مطالب آن بدون دسته‌بندی باقی ماندند.', 'info')
    return redirect(url_for('articles_admin.categories', section=section))


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
        db.session.commit()
        return jsonify({'location': image_url(filename)})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
