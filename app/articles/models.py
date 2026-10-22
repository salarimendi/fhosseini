# -*- coding: utf-8 -*-
"""
app/articles/models.py

مدل‌های مربوط به ماژول مقالات - کاملاً مجزا از app/models.py اصلی.
چون db (نمونه‌ی SQLAlchemy) در app/__init__.py ساخته می‌شود، همان‌جا import
می‌کنیم؛ به این ترتیب هیچ خطی از app/models.py تغییر نمی‌کند.

برای این‌که Flask-Migrate این مدل‌ها را ببیند، کافی است این فایل در جایی از
مسیر startup برنامه import شود - این اتفاق خودکار می‌افتد چون
app/articles/routes_admin.py و routes_public.py این ماژول را import
می‌کنند و آن دو هم توسط register_articles(app) که در app/routes/__init__.py
صدا زده می‌شود import می‌شوند (به INSTALL.md نگاه کنید).
"""

from datetime import datetime
from app import db


# بخش‌های محتوا: «مقالات» و «وبلاگ فعالیت‌ها» از یک ساختار (مدل، پنل، ویرایشگر) استفاده می‌کنند
# و فقط با ستون section از هم جدا می‌شوند؛ افزودن بخش جدید فقط افزودن یک مقدار به SECTIONS است.
SECTION_ARTICLES = 'articles'
SECTION_ACTIVITIES = 'activities'
SECTIONS = (SECTION_ARTICLES, SECTION_ACTIVITIES)


class ArticleCategory(db.Model):
    """
    دسته‌بندی مقالات.
    عمداً اسمش ArticleCategory گذاشته شده (نه فقط Category) تا با هیچ مدل
    احتمالی دیگری در پروژه (مثلاً دسته‌بندی اشعار) تداخل نام پیدا نکند.
    """
    __tablename__ = 'article_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    section = db.Column(db.String(20), nullable=False, default=SECTION_ARTICLES,
                        server_default=SECTION_ARTICLES, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    articles = db.relationship('Article', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<ArticleCategory {self.name}>'


class Article(db.Model):
    """مقاله"""
    __tablename__ = 'articles'

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)

    excerpt = db.Column(db.String(500), nullable=True)
    content_html = db.Column(db.Text, nullable=False)

    # فقط نام فایل ذخیره می‌شود (نه کل URL) تا اگر مسیر آپلود جابه‌جا شد،
    # لازم نباشد رکوردهای دیتابیس آپدیت شوند. آدرس نهایی در زمان نمایش با
    # url_for('articles_public.media', filename=...) ساخته می‌شود.
    featured_image_filename = db.Column(db.String(255), nullable=True)

    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)
    meta_keywords = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), nullable=False, default=STATUS_DRAFT, index=True)
    views = db.Column(db.Integer, default=0, nullable=False)

    # نکته مهم: 'users.id' فرض می‌کند نام جدول کاربر شما 'users' است.
    # اگر در app/models.py کلاس User بدون __tablename__ صریح تعریف شده،
    # SQLAlchemy پیش‌فرض آن را 'user' (مفرد) می‌سازد نه 'users'.
    # قبل از اجرای migration، این مقدار را با نام واقعی جدول کاربرتان چک کنید:
    #   >>> from app.models import User; print(User.__tablename__)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('article_categories.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, nullable=True)

    author = db.relationship('User', backref='articles')
    category = db.relationship('ArticleCategory', back_populates='articles')

    def __repr__(self):
        return f'<Article {self.title}>'

    @property
    def content_html_display(self):
        """HTML برای نمایش؛ آدرس تصاویر قدیمیِ نسبی را هم به /articles/media/... اصلاح می‌کند."""
        from app.articles.utils import normalize_media_urls
        return normalize_media_urls(self.content_html)

    @property
    def contributors_list(self):
        return [line.strip() for line in (self.contributors or '').splitlines() if line.strip()]

    @property
    def video_embed_url(self):
        from app.articles.utils import video_embed_url
        return video_embed_url(self.video_url)

    @property
    def is_published(self):
        return self.status == self.STATUS_PUBLISHED

    def publish(self):
        self.status = self.STATUS_PUBLISHED
        if not self.published_at:
            self.published_at = datetime.utcnow()

    def get_meta_title(self):
        return self.meta_title or self.title

    def get_meta_description(self):
        return self.meta_description or self.excerpt or ''


class ArticleMedia(db.Model):
    """
    رکورد دیتابیسی هر فایل مدیای مقاله. خود فایل فقط در پوشه‌ی uploads
    (ARTICLE_IMAGE_UPLOAD_FOLDER) نگهداری می‌شود و اینجا فقط نام و متادیتای آن است.
    article_id تا زمان ذخیره‌ی مقاله (مثلاً آپلود از داخل ویرایشگر) می‌تواند خالی باشد.
    """
    __tablename__ = 'article_media'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=True, index=True)
    filename = db.Column(db.String(255), unique=True, nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    article = db.relationship('Article', backref=db.backref('media', lazy='dynamic'))
