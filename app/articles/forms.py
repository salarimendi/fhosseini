# -*- coding: utf-8 -*-
"""
app/articles/forms.py
کاملاً مجزا از app/forms.py اصلی - نیازی به تغییر آن فایل نیست.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class ArticleCategoryForm(FlaskForm):
    name = StringField('نام دسته‌بندی', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('توضیحات', validators=[Optional(), Length(max=1000)])


class ArticleForm(FlaskForm):
    # --- فقط برای «وبلاگ فعالیت‌ها» (در بخش مقالات نمایش داده نمی‌شوند) ---
    stage_label = StringField('عنوان مرحله (مثلاً «مرحله ۲: تصحیح نسخه‌ها»)', validators=[Optional(), Length(max=120)])
    contributors = TextAreaField('مشارکت‌کنندگان (هر نفر در یک خط)', validators=[Optional(), Length(max=2000)])
    video_url = StringField('لینک ویدیو (آپارات یا یوتیوب)', validators=[Optional(), Length(max=500)])

    def validate_video_url(self, field):
        from app.articles.utils import video_embed_url
        if field.data and not video_embed_url(field.data):
            raise ValidationError('فقط لینک ویدیوی آپارات (aparat.com/v/…) یا یوتیوب پذیرفته می‌شود.')

    title = StringField('عنوان مقاله', validators=[DataRequired(), Length(max=255)])

    category_id = SelectField('دسته‌بندی', coerce=int, validators=[Optional()])

    featured_image = FileField(
        'تصویر شاخص',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'فقط فایل تصویری مجاز است')],
    )

    # TinyMCE این textarea را جایگزین می‌کند (به editor.html و article-editor.js نگاه کنید)
    content_html = TextAreaField('محتوای مقاله', validators=[DataRequired()])

    excerpt = TextAreaField('خلاصه (اختیاری)', validators=[Optional(), Length(max=500)])

    meta_title = StringField('عنوان متا / SEO (اختیاری)', validators=[Optional(), Length(max=255)])
    meta_description = TextAreaField('توضیح متا / SEO (اختیاری)', validators=[Optional(), Length(max=500)])
    meta_keywords = StringField('کلمات کلیدی (با کاما جدا کنید)', validators=[Optional(), Length(max=255)])

    status = SelectField(
        'وضعیت',
        choices=[('draft', 'پیش‌نویس'), ('published', 'منتشرشده')],
        default='draft',
    )
