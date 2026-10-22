"""
تبدیل تصاویر آپلودی به WebP (مشترک بین مستندات پژوهشی، مقالات و اسکریپت
scripts/convert_images_to_webp.py).

این ماژول عمداً به Flask/SQLAlchemy وابسته نیست تا اسکریپت مستقل هم بتواند
آن را از روی مسیر فایل بارگذاری کند. تنها وابستگی: Pillow.

قواعد ایمنی:
- فایلی که Pillow نتواند آن را به‌عنوان تصویر معتبر باز کند، ValueError می‌دهد.
- تصاویر متحرک (GIF/WebP متحرک) تبدیل نمی‌شوند و همان فایل اصلی نگه داشته می‌شود.
- اگر خود فایل WebP ثابت باشد، بازرمزگذاری نمی‌شود (جلوگیری از افت کیفیت).
- ابعاد بزرگ‌تر از MAX_SIDE با حفظ نسبت کوچک می‌شود (کاهش حجم و بار CPU).
"""
import io
from collections import namedtuple

from PIL import Image, ImageOps

WEBP_QUALITY = 82
WEBP_METHOD = 4            # تعادل سرعت/حجم؛ ~۰٫۳–۱ ثانیه برای عکس‌های معمول
MAX_SIDE = 2560
MAX_PIXELS = 50_000_000    # محافظت در برابر تصاویر بسیار بزرگ (decompression bomb)

Converted = namedtuple('Converted', 'data ext mime converted')


def _has_alpha(img):
    return img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)


def convert_bytes_to_webp(data, quality=WEBP_QUALITY, max_side=MAX_SIDE):
    """
    data (bytes) → Converted(data, ext, mime, converted).
    converted=False یعنی بایت‌های اصلی با پسوند اصلی برگردانده شده‌اند (تصویر متحرک)
    یا ورودی از قبل WebP ثابت بوده است.
    """
    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or '').upper()
        width, height = img.size
    except Exception as exc:
        raise ValueError('فایل، تصویر معتبری نیست.') from exc

    if width * height > MAX_PIXELS:
        raise ValueError('ابعاد تصویر بیش از حد بزرگ است.')

    animated = getattr(img, 'is_animated', False) and getattr(img, 'n_frames', 1) > 1
    if animated:
        ext = {'GIF': 'gif', 'WEBP': 'webp', 'PNG': 'png'}.get(fmt, 'gif')
        return Converted(data, ext, Image.MIME.get(fmt, 'image/gif'), False)

    if fmt == 'WEBP' and max(width, height) <= max_side:
        return Converted(data, 'webp', 'image/webp', False)

    img.load()
    img = ImageOps.exif_transpose(img)
    if img.mode == 'CMYK':
        img = img.convert('RGB')
    elif _has_alpha(img):
        img = img.convert('RGBA')
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side), Image.LANCZOS)

    out = io.BytesIO()
    kwargs = {'quality': quality, 'method': WEBP_METHOD}
    icc = img.info.get('icc_profile')
    if icc:
        kwargs['icc_profile'] = icc
    img.save(out, 'WEBP', **kwargs)
    return Converted(out.getvalue(), 'webp', 'image/webp', True)


def convert_file_to_webp(src_path, dst_path, **kwargs):
    """فایل را می‌خواند، تبدیل می‌کند و در dst_path می‌نویسد (src دست‌نخورده). Converted برمی‌گرداند."""
    with open(src_path, 'rb') as fh:
        result = convert_bytes_to_webp(fh.read(), **kwargs)
    with open(dst_path, 'wb') as fh:
        fh.write(result.data)
    return result


SavedImage = namedtuple('SavedImage', 'filename size mime converted')


def save_upload(file_storage, folder, base_name, original_ext, convert=True, **kwargs):
    """
    آپلود Flask (FileStorage) را در folder ذخیره می‌کند.
    convert=True → WebP (یا فایل اصلی برای تصویر متحرک)؛ False → ذخیره‌ی عین فایل با original_ext.
    خروجی: SavedImage(filename, size, mime, converted)
    """
    import os
    os.makedirs(folder, exist_ok=True)
    if not convert:
        filename = f'{base_name}.{original_ext}'
        file_storage.save(os.path.join(folder, filename))
        size = os.path.getsize(os.path.join(folder, filename))
        return SavedImage(filename, size, file_storage.mimetype, False)

    file_storage.stream.seek(0)
    result = convert_bytes_to_webp(file_storage.stream.read(), **kwargs)
    filename = f'{base_name}.{result.ext}'
    path = os.path.join(folder, filename)
    tmp = path + '.tmp'
    with open(tmp, 'wb') as fh:          # نوشتن اتمیک: فایل نیمه‌کاره هرگز نمایش داده نمی‌شود
        fh.write(result.data)
    os.replace(tmp, path)
    return SavedImage(filename, len(result.data), result.mime, result.converted)
