# -*- coding: utf-8 -*-
"""
app/articles/utils.py
ابزارهای کمکی ماژول مقالات: تولید slug فارسی و پاکسازی HTML.
کاملاً مجزا از app/utils/*.py موجود پروژه - چیزی از آن‌ها استفاده یا تغییر نمی‌کند.

نیازمند: pip install python-slugify bleach
"""

import re
import bleach
from slugify import slugify as _slugify


# ---------------------------------------------------------------------------
# Slug فارسی یکتا
# ---------------------------------------------------------------------------
def make_slug(text):
    """تبدیل متن فارسی/انگلیسی به slug امن برای URL."""
    return _slugify(text, allow_unicode=True, lowercase=True)


def unique_slug(text, model, slug_field='slug', instance_id=None):
    """
    یک slug یکتا برای مدل داده‌شده می‌سازد (مثل وردپرس: با پسوند -2, -3 و...
    اگر تکراری بود).
    """
    base_slug = make_slug(text) or 'item'
    slug = base_slug
    counter = 2

    query = model.query.filter(getattr(model, slug_field) == slug)
    if instance_id is not None:
        query = query.filter(model.id != instance_id)

    while query.first() is not None:
        slug = f'{base_slug}-{counter}'
        counter += 1
        query = model.query.filter(getattr(model, slug_field) == slug)
        if instance_id is not None:
            query = query.filter(model.id != instance_id)

    return slug


# ---------------------------------------------------------------------------
# پاکسازی HTML خروجی ویرایشگر (جلوگیری از XSS ذخیره‌شده)
# ---------------------------------------------------------------------------
ALLOWED_TAGS = [
    'p', 'br', 'hr', 'span', 'div',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'b', 'em', 'i', 'u', 's', 'sub', 'sup',
    'ul', 'ol', 'li',
    'a', 'img', 'figure', 'figcaption',
    'blockquote', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    '*': ['class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(raw_html):
    """HTML خروجی ویرایشگر را قبل از ذخیره پاکسازی می‌کند."""
    if not raw_html:
        return ''

    cleaned = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    # لینک‌های target="_blank" را در برابر tabnabbing امن‌تر کن
    cleaned = re.sub(
        r'<a ([^>]*?)target="_blank"([^>]*)>',
        r'<a \1target="_blank" rel="noopener noreferrer"\2>',
        cleaned,
    )
    return cleaned


def html_to_excerpt(raw_html, max_length=160):
    """اگر خلاصه دستی وارد نشده باشد، از روی محتوا یک excerpt کوتاه می‌سازد."""
    if not raw_html:
        return ''
    text_only = re.sub(r'<[^>]+>', ' ', raw_html)
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    if len(text_only) <= max_length:
        return text_only
    return text_only[:max_length].rsplit(' ', 1)[0] + '…'
