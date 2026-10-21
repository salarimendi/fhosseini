# -*- coding: utf-8 -*-
"""
app/articles/utils.py
ابزارهای کمکی ماژول مقالات: تولید slug فارسی و پاکسازی HTML.
کاملاً مجزا از app/utils/*.py موجود پروژه - چیزی از آن‌ها استفاده یا تغییر نمی‌کند.

نیازمند: pip install python-slugify bleach
"""

import base64
import binascii
import os
import re
import uuid

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


# ---------------------------------------------------------------------------
# نرمال‌سازی آدرس تصاویر داخل متن
# ---------------------------------------------------------------------------
# ریشه‌ی مشکل «تصویر بعد از ذخیره/بارگذاری مجدد نمایش داده نمی‌شود»:
#  1) TinyMCE به‌صورت پیش‌فرض آدرس‌ها را نسبی می‌کند (مثلاً
#     ../../articles/media/x.png نسبت به /admin/articles/new). همان مقدار
#     در دیتابیس ذخیره می‌شد و در /articles/<slug> به مسیر اشتباه می‌رفت.
#  2) تصاویر چسبانده‌شده (data:image/...;base64) توسط bleach حذف می‌شدند چون
#     پروتکل data مجاز نبود؛ در نتیجه src خالی می‌شد.
MEDIA_URL_PREFIX = '/articles/media/'
_MEDIA_SRC_RE = re.compile(
    r'^(?:https?://[^/]+)?(?:/?(?:\.\./|\./)*)(?:admin/)?(?:articles/)?media/([^?#"\']+)',
    re.IGNORECASE,
)
_IMG_SRC_RE = re.compile(
    r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)\2',
    re.IGNORECASE | re.DOTALL,
)
_DATA_URI_RE = re.compile(
    r'^data:image/(png|jpe?g|gif|webp);base64,(.+)$', re.IGNORECASE | re.DOTALL
)


def normalize_media_urls(raw_html, upload_folder=None, max_bytes=5 * 1024 * 1024):
    """
    - آدرس‌های نسبی/مطلق تصاویر مقاله را به شکل ثابت /articles/media/<file> درمی‌آورد.
    - اگر upload_folder داده شود، تصاویر data:URI را به فایل تبدیل و ذخیره می‌کند.
    """
    if not raw_html:
        return ''

    def _repl(match):
        prefix, quote, src = match.group(1), match.group(2), match.group(3).strip()

        media = _MEDIA_SRC_RE.match(src)
        if media:
            return f'{prefix}{quote}{MEDIA_URL_PREFIX}{media.group(1)}{quote}'

        data = _DATA_URI_RE.match(src)
        if data and upload_folder:
            ext = data.group(1).lower().replace('jpeg', 'jpg')
            try:
                payload = base64.b64decode(re.sub(r'\s+', '', data.group(2)), validate=True)
            except (binascii.Error, ValueError):
                return match.group(0)
            if len(payload) > max_bytes:
                return match.group(0)
            os.makedirs(upload_folder, exist_ok=True)
            name = f'{uuid.uuid4().hex}.{ext}'
            with open(os.path.join(upload_folder, name), 'wb') as fh:
                fh.write(payload)
            return f'{prefix}{quote}{MEDIA_URL_PREFIX}{name}{quote}'

        return match.group(0)

    return _IMG_SRC_RE.sub(_repl, raw_html)


def extract_media_filenames(html):
    """نام فایل تصاویر داخل متن که روی سرور مقاله‌اند (برای پاکسازی هنگام حذف)."""
    if not html:
        return set()
    return set(re.findall(r'/articles/media/([\w.\-]+)', html))


def sanitize_html(raw_html, upload_folder=None):
    """HTML خروجی ویرایشگر را قبل از ذخیره پاکسازی می‌کند."""
    if not raw_html:
        return ''

    raw_html = normalize_media_urls(raw_html, upload_folder)

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


# ---------------------------------------------------------------------------
# پاکسازی فایل‌ها (فقط تصاویر/مدیا؛ خود مقاله و متادیتا در دیتابیس است)
# ---------------------------------------------------------------------------
def remove_media_file(upload_folder, filename):
    """حذف امن یک فایل از پوشه‌ی uploads مقالات (فقط نام ساده، بدون مسیر)."""
    if not filename or os.path.basename(filename) != filename:
        return
    try:
        os.remove(os.path.join(upload_folder, filename))
    except FileNotFoundError:
        pass
