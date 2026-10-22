"""
تست‌های ایمنی تبدیل تصاویر به WebP: ماژول app/utils/images.py و اسکریپت
scripts/convert_images_to_webp.py (مستقل از Flask؛ فقط Pillow + sqlite3).
"""
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


images = _load('webp_images_t', 'app/utils/images.py')
script = _load('webp_script_t', 'scripts/convert_images_to_webp.py')


def make_image(fmt, size=(900, 600), mode='RGB', **save):
    import random
    rnd = random.Random(5)
    im = Image.new(mode, size)
    px = im.load()
    for x in range(0, size[0]):
        for y in range(0, size[1], 3):
            v = (x * 255 // size[0], y * 255 // size[1], rnd.randrange(256))
            px[x, y] = v if mode == 'RGB' else v + (200,)
    buf = io.BytesIO()
    im.save(buf, fmt, **save)
    return buf.getvalue()


class ImagesModuleTest(unittest.TestCase):
    def test_jpeg_png_become_webp_and_smaller(self):
        jpg = make_image('JPEG', quality=95)
        r = images.convert_bytes_to_webp(jpg)
        self.assertTrue(r.converted)
        self.assertEqual((r.ext, r.mime), ('webp', 'image/webp'))
        self.assertLess(len(r.data), len(jpg))
        self.assertEqual(Image.open(io.BytesIO(r.data)).format, 'WEBP')

    def test_alpha_is_kept(self):
        r = images.convert_bytes_to_webp(make_image('PNG', mode='RGBA'))
        self.assertIn('A', Image.open(io.BytesIO(r.data)).mode)

    def test_large_image_is_downscaled(self):
        r = images.convert_bytes_to_webp(make_image('JPEG', size=(3000, 1000)), max_side=1000)
        self.assertEqual(Image.open(io.BytesIO(r.data)).size, (1000, 333))

    def test_animated_gif_and_webp_passthrough_and_invalid(self):
        frames = [Image.new('RGB', (40, 40), c) for c in ('red', 'blue')]
        buf = io.BytesIO()
        frames[0].save(buf, 'GIF', save_all=True, append_images=frames[1:], duration=100, loop=0)
        r = images.convert_bytes_to_webp(buf.getvalue())
        self.assertEqual((r.converted, r.ext, r.data), (False, 'gif', buf.getvalue()))
        w = make_image('WEBP')
        r = images.convert_bytes_to_webp(w)
        self.assertEqual((r.converted, r.ext, r.data), (False, 'webp', w))
        with self.assertRaises(ValueError):
            images.convert_bytes_to_webp(b'not an image')


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.rdir = self.tmp / 'uploads' / 'research_images'
        self.adir = self.tmp / 'uploads' / 'articles_images'
        self.rdir.mkdir(parents=True)
        self.adir.mkdir(parents=True)
        self.db = self.tmp / 'test.db'
        (self.rdir / 'doc1.jpg').write_bytes(make_image('JPEG', quality=95))
        (self.rdir / 'doc2.png').write_bytes(make_image('PNG'))
        (self.rdir / 'doc1.png').write_bytes(make_image('PNG', size=(700, 500)))   # هم‌نام (stem) با doc1.jpg
        (self.rdir / 'done.webp').write_bytes(make_image('WEBP'))
        (self.rdir / 'broken.jpg').write_bytes(b'garbage')
        (self.adir / 'a1.jpg').write_bytes(make_image('JPEG', quality=95))
        (self.adir / 'a2.png').write_bytes(make_image('PNG'))
        conn = sqlite3.connect(self.db)
        conn.executescript('''
            CREATE TABLE research_images (id INTEGER PRIMARY KEY, comment_id INT, filename TEXT, file_size INT, caption TEXT);
            CREATE TABLE articles (id INTEGER PRIMARY KEY, featured_image_filename TEXT, content_html TEXT);
            CREATE TABLE article_media (id INTEGER PRIMARY KEY, filename TEXT UNIQUE, mime_type TEXT, size_bytes INT);
        ''')
        conn.executemany('INSERT INTO research_images(comment_id,filename,file_size,caption) VALUES (1,?,?,?)', [
            ('doc1.jpg', 1, 'c1'), ('doc2.png', 1, 'c2'), ('doc1.png', 1, 'c3'),
            ('done.webp', 1, 'c4'), ('broken.jpg', 1, 'c5'), ('missing.jpg', 1, 'c6')])
        conn.execute("INSERT INTO articles VALUES (1,'a1.jpg',?)",
                     ('<p><img src="/articles/media/a2.png"><img src="/articles/media/a2.png.bak"></p>',))
        conn.executemany('INSERT INTO article_media(filename,mime_type,size_bytes) VALUES (?,?,?)',
                         [('a1.jpg', 'image/jpeg', 9), ('a2.png', 'image/png', 9)])
        conn.commit()
        conn.close()
        self.args = ['--root', str(ROOT), '--db', str(self.db), '--research-dir', str(self.rdir),
                     '--articles-dir', str(self.adir), '--backup-dir', str(self.tmp / 'backups')]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def q(self, sql):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(sql).fetchall()
        finally:
            conn.close()

    def run_cmd(self, *cmd):
        return script.main(list(cmd) + self.args)

    def run_dir(self):
        return sorted((self.tmp / 'backups').glob('webp_migration_*'))[-1]

    def check_consistency(self):
        """هر نام فایل در دیتابیس روی دیسک وجود دارد و تصویر معتبر است."""
        names = [(self.rdir, r[0]) for r in self.q('SELECT filename FROM research_images')]
        names += [(self.adir, r[0]) for r in self.q('SELECT filename FROM article_media')]
        names += [(self.adir, r[0]) for r in self.q('SELECT featured_image_filename FROM articles')]
        for folder, name in names:
            if name in ('missing.jpg', 'broken.jpg'):
                continue
            self.assertTrue((folder / name).is_file(), name)

    def test_scan_changes_nothing(self):
        before = sorted(os.listdir(self.rdir))
        self.assertEqual(self.run_cmd('scan'), 0)
        self.assertEqual(sorted(os.listdir(self.rdir)), before)
        self.assertFalse((self.tmp / 'backups').exists())

    def test_convert_idempotent_finalize_rollback(self):
        orig_db = self.q('SELECT filename FROM research_images ORDER BY id')
        code = self.run_cmd('convert')
        self.assertEqual(code, 2)                       # broken.jpg خطا می‌دهد؛ بقیه موفق
        run = self.run_dir()
        manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
        done = {e['old']: e['new'] for e in manifest['entries']}
        self.assertEqual(set(done), {'doc1.jpg', 'doc2.png', 'doc1.png', 'a1.jpg', 'a2.png'})
        self.assertEqual(len(set(done.values())), 5)    # برخورد نام doc1.jpg/doc1.png حل شد
        self.assertTrue((run / 'db_before.sqlite').is_file())
        for e in manifest['entries']:
            self.assertTrue((run / 'files' / e['kind'] / e['old']).is_file())     # کپی پشتیبان
            self.assertTrue((Path(e['folder']) / e['old']).is_file())             # اصلی هنوز هست
        self.check_consistency()
        # ارجاع‌های دیتابیس
        self.assertEqual(self.q('SELECT filename FROM research_images WHERE caption="c4"')[0][0], 'done.webp')
        self.assertEqual(self.q('SELECT filename FROM research_images WHERE caption="c6"')[0][0], 'missing.jpg')
        self.assertTrue(self.q('SELECT featured_image_filename FROM articles')[0][0].endswith('.webp'))
        html = self.q('SELECT content_html FROM articles')[0][0]
        self.assertIn(f'/articles/media/{done["a2.png"]}"', html)
        self.assertIn('/articles/media/a2.png.bak', html)                         # نام مشابه خراب نشد
        self.assertEqual(self.q('SELECT mime_type FROM article_media WHERE filename LIKE "a1%"')[0][0], 'image/webp')
        # اجرای مجدد: تبدیل تکراری ندارد
        before_runs = len(list((self.tmp / 'backups').glob('webp_migration_*')))
        self.run_cmd('convert')
        self.assertEqual(self.q('SELECT COUNT(*) FROM research_images')[0][0], 6)
        self.check_consistency()
        # finalize: اصلی‌ها از uploads حذف، کپی پشتیبان می‌ماند
        self.assertEqual(script.main(['finalize', '--run', str(run)] + self.args), 0)
        for e in manifest['entries']:
            self.assertFalse((Path(e['folder']) / e['old']).exists())
            self.assertTrue((run / 'files' / e['kind'] / e['old']).is_file())
        self.check_consistency()
        # rollback: همه‌چیز مثل قبل
        self.assertEqual(script.main(['rollback', '--run', str(run)] + self.args), 0)
        self.assertEqual(self.q('SELECT filename FROM research_images ORDER BY id'), orig_db)
        self.assertEqual(self.q('SELECT featured_image_filename FROM articles')[0][0], 'a1.jpg')
        self.assertIn('/articles/media/a2.png"', self.q('SELECT content_html FROM articles')[0][0])
        for e in manifest['entries']:
            self.assertTrue((Path(e['folder']) / e['old']).is_file())
            self.assertFalse((Path(e['folder']) / e['new']).exists())

    def test_failed_db_step_leaves_everything_untouched(self):
        conn = sqlite3.connect(self.db)
        conn.execute('DROP TABLE article_media')
        conn.execute("CREATE TABLE article_media (id INTEGER PRIMARY KEY, filename TEXT UNIQUE, mime_type TEXT, size_bytes INT)")
        conn.execute("INSERT INTO article_media(filename) VALUES ('a1.webp')")   # برخورد یکتایی → خطای تراکنش
        conn.execute("INSERT INTO article_media(filename) VALUES ('a1.jpg')")
        conn.commit()
        conn.close()
        before = {p.name for p in self.adir.iterdir()}
        self.assertEqual(self.run_cmd('convert'), 1)
        self.assertEqual({p.name for p in self.adir.iterdir()}, before)           # webp ساخته‌شده پاک شد
        self.assertEqual(self.q('SELECT featured_image_filename FROM articles')[0][0], 'a1.jpg')


if __name__ == '__main__':
    unittest.main()
