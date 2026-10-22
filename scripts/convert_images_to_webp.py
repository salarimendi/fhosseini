#!/usr/bin/env python3
"""
تبدیل تصاویر قبلی پروژه (مستندات پژوهشی و مقالات) به WebP — هم فایل‌ها، هم ارجاعات دیتابیس.

مستقل از Flask است (فقط Pillow + sqlite3). اجرا از ریشه‌ی پروژه:

    python scripts/convert_images_to_webp.py scan                 # فقط گزارش (هیچ تغییری نمی‌دهد)
    python scripts/convert_images_to_webp.py convert              # پشتیبان + تبدیل + به‌روزرسانی دیتابیس
    python scripts/convert_images_to_webp.py finalize --run <پوشه>  # پس از تأیید: حذف اصلی‌ها از uploads
    python scripts/convert_images_to_webp.py rollback --run <پوشه>  # بازگردانی کامل همان اجرا

ایمنی:
- convert هرگز فایل اصلی را حذف نمی‌کند. قبل از هر کاری، نسخه‌ی دیتابیس (db_before.sqlite) و
  کپی همه‌ی فایل‌های اصلی در backups/webp_migration_<زمان>/ ساخته می‌شود.
- به‌روزرسانی دیتابیس در یک تراکنش انجام می‌شود و پیش از commit بررسی می‌شود که هر ارجاع به فایل
  موجودِ معتبر اشاره کند؛ در غیر این صورت rollback می‌شود.
- حذف اصلی‌ها فقط با finalize و پس از بازبررسی کامل (فایل جدید معتبر، ارجاع دیتابیس، کپی پشتیبان).
- اجرای مجدد امن است: فایل‌های webp و تبدیل‌شده‌ها دوباره تبدیل نمی‌شوند.
- تصاویر متحرک، فایل‌های خراب/ناموجود و فایل‌هایی که WebP‌شان بزرگ‌تر می‌شود، دست‌نخورده می‌مانند و گزارش می‌شوند.

فقط دیتابیس SQLite پشتیبانی می‌شود (پیش‌فرض پروژه).
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:                                   # pragma: no cover
    sys.exit('Pillow نصب نیست: pip install Pillow')

ROOT = Path(__file__).resolve().parent.parent
CONVERTIBLE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff'}
MEDIA_PREFIX = '/articles/media/'


# ---------------------------------------------------------------------------
# تنظیمات و مسیرها
# ---------------------------------------------------------------------------
def load_images_module(root):
    """ماژول مشترک تبدیل (app/utils/images.py) را بدون import کردن بسته‌ی app بارگذاری می‌کند."""
    path = Path(root) / 'app' / 'utils' / 'images.py'
    spec = importlib.util.spec_from_file_location('webp_images', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_env_file(root):
    values = {}
    env_path = Path(root) / '.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def resolve_settings(args):
    root = Path(args.root).resolve()
    env = {**read_env_file(root), **{k: v for k, v in os.environ.items() if k in (
        'DATABASE_URL', 'RESEARCH_IMAGE_UPLOAD_FOLDER', 'ARTICLE_IMAGE_UPLOAD_FOLDER')}}

    def folder(cli, key, default):
        p = Path(cli or env.get(key) or default)
        return p if p.is_absolute() else root / p

    db_path = args.db
    if not db_path:
        url = env.get('DATABASE_URL', 'sqlite:///instance/ferdosi.db')
        if not url.startswith('sqlite:///'):
            sys.exit('فقط SQLite پشتیبانی می‌شود؛ مسیر دیتابیس را با --db بدهید.')
        db_path = url[len('sqlite:///'):]
    db = Path(db_path)
    if not db.is_absolute():
        candidates = [root / db, root / 'instance' / db]
        db = next((c for c in candidates if c.exists()), candidates[0])
    if not db.exists():
        sys.exit(f'فایل دیتابیس پیدا نشد: {db}')

    return {
        'root': root,
        'db': db,
        'research_dir': folder(args.research_dir, 'RESEARCH_IMAGE_UPLOAD_FOLDER', 'uploads/research_images'),
        'article_dir': folder(args.articles_dir, 'ARTICLE_IMAGE_UPLOAD_FOLDER', 'uploads/articles_images'),
        'backup_root': Path(args.backup_dir).resolve() if args.backup_dir else root / 'backups',
    }


# ---------------------------------------------------------------------------
# دیتابیس
# ---------------------------------------------------------------------------
def connect(db_path):
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def backup_database(db_path, dest):
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(dest))
    with dst:
        src.backup(dst)
    src.close()
    dst.close()


def collect_references(conn):
    """
    همه‌ی ارجاعات دیتابیس به تصاویر: {'research': {filename}, 'article': {filename}}
    (برای مقالات: article_media، تصویر شاخص و ارجاع‌های /articles/media/ داخل متن).
    """
    refs = {'research': set(), 'article': set()}
    if has_table(conn, 'research_images'):
        refs['research'] |= {r['filename'] for r in conn.execute('SELECT filename FROM research_images') if r['filename']}
    if has_table(conn, 'article_media'):
        refs['article'] |= {r['filename'] for r in conn.execute('SELECT filename FROM article_media') if r['filename']}
    if has_table(conn, 'articles'):
        for r in conn.execute('SELECT featured_image_filename, content_html FROM articles'):
            if r['featured_image_filename']:
                refs['article'].add(r['featured_image_filename'])
            refs['article'] |= set(re.findall(re.escape(MEDIA_PREFIX) + r'([\w.\-]+)', r['content_html'] or ''))
    return refs


def replace_media_name(html, old, new):
    return re.sub(re.escape(MEDIA_PREFIX + old) + r'(?![\w.\-])', MEDIA_PREFIX + new, html)


def apply_db_change(conn, kind, old, new, new_size, new_mime, old_size, old_mime):
    """نام فایل را در همه‌ی جدول‌ها از old به new تغییر می‌دهد؛ تعداد ردیف‌های تغییریافته را برمی‌گرداند."""
    changed = 0
    if kind == 'research' and has_table(conn, 'research_images'):
        cur = conn.execute('UPDATE research_images SET filename=?, file_size=? WHERE filename=?', (new, new_size, old))
        changed += cur.rowcount
    if kind == 'article':
        if has_table(conn, 'article_media'):
            cur = conn.execute('UPDATE article_media SET filename=?, mime_type=?, size_bytes=? WHERE filename=?',
                               (new, new_mime, new_size, old))
            changed += cur.rowcount
        if has_table(conn, 'articles'):
            cur = conn.execute('UPDATE articles SET featured_image_filename=? WHERE featured_image_filename=?', (new, old))
            changed += cur.rowcount
            for row in conn.execute('SELECT id, content_html FROM articles WHERE content_html LIKE ?',
                                    (f'%{MEDIA_PREFIX}{old}%',)).fetchall():
                updated = replace_media_name(row['content_html'], old, new)
                if updated != row['content_html']:
                    conn.execute('UPDATE articles SET content_html=? WHERE id=?', (updated, row['id']))
                    changed += 1
    return changed


# ---------------------------------------------------------------------------
# منطق تبدیل
# ---------------------------------------------------------------------------
def folder_for(settings, kind):
    return settings['research_dir'] if kind == 'research' else settings['article_dir']


def plan_conversions(settings, refs, images):
    """فهرست اقدام‌ها + مواردی که نادیده گرفته می‌شوند (با دلیل)."""
    plan, skipped = [], []
    for kind in ('research', 'article'):
        folder = folder_for(settings, kind)
        for name in sorted(refs[kind]):
            ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            if ext == 'webp':
                continue
            if ext not in CONVERTIBLE_EXTS:
                skipped.append({'kind': kind, 'file': name, 'reason': f'پسوند پشتیبانی‌نشده ({ext or "بدون پسوند"})'})
                continue
            src = folder / name
            if not src.is_file():
                skipped.append({'kind': kind, 'file': name, 'reason': 'فایل روی دیسک پیدا نشد'})
                continue
            plan.append({'kind': kind, 'old': name, 'folder': str(folder)})
    return plan, skipped


def choose_target(folder, old, data, existing_new_names):
    """نام هدف: stem.webp؛ اگر موجود و متفاوت بود stem-ext.webp. فایل موجودِ هم‌محتوا دوباره استفاده می‌شود."""
    stem, _, ext = old.rpartition('.')
    for candidate in (f'{stem}.webp', f'{stem}-{ext.lower()}.webp'):
        path = folder / candidate
        if candidate in existing_new_names:
            continue
        if not path.exists():
            return candidate, False
        if path.read_bytes() == data:
            return candidate, True          # بقایای اجرای قبلیِ ناتمام؛ همان خروجی
    raise RuntimeError(f'نام هدف برای {old} پیدا نشد')


def verify_webp(path):
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        if im.format != 'WEBP':
            raise ValueError('فرمت فایل جدید WebP نیست')
        return im.size


def save_manifest(run_dir, manifest):
    tmp = run_dir / 'manifest.json.tmp'
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, run_dir / 'manifest.json')


def load_manifest(run_dir):
    path = Path(run_dir) / 'manifest.json'
    if not path.exists():
        sys.exit(f'manifest.json در {run_dir} پیدا نشد.')
    return json.loads(path.read_text(encoding='utf-8'))


def cmd_scan(settings, images):
    conn = connect(settings['db'])
    refs = collect_references(conn)
    plan, skipped = plan_conversions(settings, refs, images)
    conn.close()
    total = sum((Path(p['folder']) / p['old']).stat().st_size for p in plan)
    print(f'ارجاع تصویر در دیتابیس: مستندات={len(refs["research"])}  مقالات={len(refs["article"])}')
    print(f'قابل تبدیل: {len(plan)} فایل ({total / 1e6:.1f} مگابایت)')
    for s in skipped:
        print(f'  نادیده: [{s["kind"]}] {s["file"]} — {s["reason"]}')
    return 0


def cmd_convert(settings, images, quality, max_side):
    conn = connect(settings['db'])
    refs = collect_references(conn)
    plan, skipped = plan_conversions(settings, refs, images)
    if not plan:
        print('چیزی برای تبدیل نیست (همه webp هستند یا قابل تبدیل نیستند).')
        for s in skipped:
            print(f'  نادیده: [{s["kind"]}] {s["file"]} — {s["reason"]}')
        conn.close()
        return 0

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # پوشه‌ی هر اجرا همیشه تازه و یکتاست؛ پشتیبان/manifest اجرای قبلی هرگز بازنویسی نمی‌شود
    run_dir = settings['backup_root'] / f'webp_migration_{stamp}'
    counter = 1
    while run_dir.exists():
        counter += 1
        run_dir = settings['backup_root'] / f'webp_migration_{stamp}_{counter}'
    (run_dir / 'files' / 'research').mkdir(parents=True)
    (run_dir / 'files' / 'article').mkdir(parents=True)

    # ۱) پشتیبان: دیتابیس + کپی فایل‌های اصلی
    backup_database(settings['db'], run_dir / 'db_before.sqlite')
    for item in plan:
        shutil.copy2(Path(item['folder']) / item['old'], run_dir / 'files' / item['kind'] / item['old'])
    print(f'پشتیبان ساخته شد: {run_dir}')

    dangling_before = {k: {n for n in refs[k] if not (folder_for(settings, k) / n).is_file()} for k in refs}
    manifest = {'created': stamp, 'db': str(settings['db']), 'entries': [], 'skipped': skipped, 'errors': [],
                'dangling_refs_before': {k: sorted(v) for k, v in dangling_before.items()}}
    created_files = []          # فقط فایل‌هایی که همین اجرا ساخته (برای پاکسازی در صورت خطا)
    new_names = set()

    # ۲) تبدیل فایل‌ها (اصلی‌ها دست‌نخورده)
    for item in plan:
        folder, old, kind = Path(item['folder']), item['old'], item['kind']
        src = folder / old
        try:
            data = src.read_bytes()
            result = images.convert_bytes_to_webp(data, quality=quality, max_side=max_side)
            if not result.converted:
                manifest['skipped'].append({'kind': kind, 'file': old, 'reason': 'تصویر متحرک؛ تبدیل نشد'})
                continue
            if len(result.data) >= len(data):
                manifest['skipped'].append({'kind': kind, 'file': old, 'reason': 'خروجی WebP بزرگ‌تر می‌شد؛ حفظ فایل اصلی'})
                continue
            target, reused = choose_target(folder, old, result.data, new_names)
            tpath = folder / target
            if not reused:
                tmp = tpath.with_suffix('.webp.tmp')
                tmp.write_bytes(result.data)
                os.replace(tmp, tpath)
                created_files.append(tpath)
            width, height = verify_webp(tpath)
            new_names.add(target)
            manifest['entries'].append({
                'kind': kind, 'old': old, 'new': target, 'folder': str(folder), 'status': 'pending',
                'old_size': len(data), 'new_size': len(result.data), 'size': [width, height],
            })
        except Exception as exc:                                  # یک فایل خراب کل کار را متوقف نمی‌کند
            manifest['errors'].append({'kind': kind, 'file': old, 'error': str(exc)})

    # ۳) به‌روزرسانی دیتابیس در یک تراکنش + بررسی پیش از commit
    try:
        conn.execute('BEGIN IMMEDIATE')
        for entry in manifest['entries']:
            old_mime = None
            if entry['kind'] == 'article' and has_table(conn, 'article_media'):
                row = conn.execute('SELECT mime_type FROM article_media WHERE filename=?', (entry['old'],)).fetchone()
                old_mime = row['mime_type'] if row else None
            entry['old_mime'] = old_mime
            entry['db_rows'] = apply_db_change(conn, entry['kind'], entry['old'], entry['new'],
                                               entry['new_size'], 'image/webp', entry['old_size'], old_mime)
        after = collect_references(conn)
        problems = []
        for kind in ('research', 'article'):
            for name in after[kind]:
                # ارجاع‌های ناموجودِ از قبل (پیش از تبدیل) خطای جدید نیستند؛ فقط گزارش می‌شوند
                if not (folder_for(settings, kind) / name).is_file() and name not in dangling_before[kind]:
                    problems.append(f'[{kind}] ارجاع دیتابیس به فایل ناموجود: {name}')
        for entry in manifest['entries']:
            if entry['old'] in after[entry['kind']]:
                problems.append(f'[{entry["kind"]}] ارجاع قدیمی هنوز باقی است: {entry["old"]}')
        if problems:
            raise RuntimeError('؛ '.join(problems[:5]))
        conn.execute('COMMIT')
    except Exception as exc:
        conn.execute('ROLLBACK')
        for path in created_files:
            path.unlink(missing_ok=True)
        manifest['errors'].append({'file': '*', 'error': f'تراکنش دیتابیس برگشت داده شد: {exc}'})
        manifest['entries'] = []
        save_manifest(run_dir, manifest)
        print(f'خطا — دیتابیس و فایل‌ها بدون تغییر ماندند: {exc}')
        conn.close()
        return 1

    for entry in manifest['entries']:
        entry['status'] = 'converted'
    save_manifest(run_dir, manifest)
    conn.close()

    saved = sum(e['old_size'] - e['new_size'] for e in manifest['entries'])
    print(f'تبدیل شد: {len(manifest["entries"])} فایل — صرفه‌جویی {saved / 1e6:.1f} مگابایت')
    for e in manifest['skipped']:
        print(f'  نادیده: [{e["kind"]}] {e["file"]} — {e["reason"]}')
    for e in manifest['errors']:
        print(f'  خطا: {e}')
    print('اصلی‌ها هنوز در uploads هستند. پس از بررسی سایت:')
    print(f'  python scripts/convert_images_to_webp.py finalize --run "{run_dir}"')
    print(f'در صورت مشکل:  python scripts/convert_images_to_webp.py rollback --run "{run_dir}"')
    return 0 if not manifest['errors'] else 2


def db_reference_count(conn, kind, name):
    n = 0
    if kind == 'research' and has_table(conn, 'research_images'):
        n += conn.execute('SELECT COUNT(*) FROM research_images WHERE filename=?', (name,)).fetchone()[0]
    if kind == 'article':
        if has_table(conn, 'article_media'):
            n += conn.execute('SELECT COUNT(*) FROM article_media WHERE filename=?', (name,)).fetchone()[0]
        if has_table(conn, 'articles'):
            n += conn.execute('SELECT COUNT(*) FROM articles WHERE featured_image_filename=?', (name,)).fetchone()[0]
            pattern = re.compile(re.escape(MEDIA_PREFIX + name) + r'(?![\w.\-])')
            for row in conn.execute('SELECT content_html FROM articles WHERE content_html LIKE ?',
                                    (f'%{MEDIA_PREFIX}{name}%',)):
                if pattern.search(row['content_html'] or ''):
                    n += 1
    return n


def cmd_finalize(settings, run_dir):
    manifest = load_manifest(run_dir)
    conn = connect(settings['db'])
    removed, problems = 0, []
    for e in manifest['entries']:
        if e['status'] != 'converted':
            continue
        folder = Path(e['folder'])
        backup_copy = Path(run_dir) / 'files' / e['kind'] / e['old']
        try:
            verify_webp(folder / e['new'])
            if db_reference_count(conn, e['kind'], e['new']) == 0 and e.get('db_rows', 0):
                raise RuntimeError('ارجاعی به نام جدید در دیتابیس نیست')
            if db_reference_count(conn, e['kind'], e['old']) != 0:
                raise RuntimeError('هنوز ارجاعی به نام قدیمی در دیتابیس هست')
            if not backup_copy.is_file():
                raise RuntimeError('کپی پشتیبان فایل اصلی موجود نیست')
        except Exception as exc:
            problems.append(f'{e["old"]}: {exc}')
            continue
        (folder / e['old']).unlink(missing_ok=True)
        e['status'] = 'finalized'
        removed += 1
    save_manifest(Path(run_dir), manifest)
    conn.close()
    print(f'اصلی‌های حذف‌شده از uploads: {removed} (کپی همه‌ی آن‌ها در {run_dir}/files می‌ماند)')
    for p in problems:
        print(f'  رد شد: {p}')
    return 0 if not problems else 2


def cmd_rollback(settings, images, run_dir):
    manifest = load_manifest(run_dir)
    conn = connect(settings['db'])
    problems, restored = [], 0
    try:
        conn.execute('BEGIN IMMEDIATE')
        for e in manifest['entries']:
            if e['status'] == 'rolled_back':
                continue
            folder = Path(e['folder'])
            backup_copy = Path(run_dir) / 'files' / e['kind'] / e['old']
            if not (folder / e['old']).is_file():
                if not backup_copy.is_file():
                    problems.append(f'اصلی و پشتیبانِ {e["old"]} هر دو موجود نیست')
                    continue
                shutil.copy2(backup_copy, folder / e['old'])
            apply_db_change(conn, e['kind'], e['new'], e['old'], e['old_size'], e.get('old_mime'), e['old_size'], None)
            e['status'] = 'rolled_back'
            restored += 1
        if problems:
            raise RuntimeError('؛ '.join(problems))
        conn.execute('COMMIT')
    except Exception as exc:
        conn.execute('ROLLBACK')
        print(f'بازگردانی انجام نشد (دیتابیس دست‌نخورده): {exc}')
        conn.close()
        return 1
    # فایل‌های webp جدید فقط وقتی دیگر ارجاعی ندارند پاک می‌شوند
    for e in manifest['entries']:
        if e['status'] == 'rolled_back' and db_reference_count(conn, e['kind'], e['new']) == 0:
            (Path(e['folder']) / e['new']).unlink(missing_ok=True)
    save_manifest(Path(run_dir), manifest)
    conn.close()
    print(f'بازگردانی شد: {restored} فایل. (نسخه‌ی کامل دیتابیس قبل از تبدیل: {run_dir}/db_before.sqlite)')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='تبدیل تصاویر قبلی پروژه به WebP (فایل + دیتابیس)')
    parser.add_argument('command', choices=['scan', 'convert', 'finalize', 'rollback'])
    parser.add_argument('--run', help='پوشه‌ی پشتیبانِ همان اجرا (برای finalize/rollback)')
    parser.add_argument('--root', default=str(ROOT), help='ریشه‌ی پروژه')
    parser.add_argument('--db', help='مسیر فایل SQLite (پیش‌فرض: از DATABASE_URL در .env)')
    parser.add_argument('--research-dir', help='پوشه‌ی تصاویر مستندات')
    parser.add_argument('--articles-dir', help='پوشه‌ی تصاویر مقالات')
    parser.add_argument('--backup-dir', help='پوشه‌ی پشتیبان‌ها (پیش‌فرض: backups/ در ریشه)')
    parser.add_argument('--quality', type=int, default=82)
    parser.add_argument('--max-side', type=int, default=2560)
    args = parser.parse_args(argv)

    settings = resolve_settings(args)
    images = load_images_module(settings['root'])
    if args.command == 'scan':
        return cmd_scan(settings, images)
    if args.command == 'convert':
        return cmd_convert(settings, images, args.quality, args.max_side)
    if not args.run:
        sys.exit('--run لازم است.')
    if args.command == 'finalize':
        return cmd_finalize(settings, args.run)
    return cmd_rollback(settings, images, args.run)


if __name__ == '__main__':
    sys.exit(main())
