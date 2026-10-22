"""وبلاگ فعالیت‌ها (بخش section='activities' از سیستم مقالات) و WebP هنگام آپلود."""
import io
import os
import unittest

from app import create_app, db
from app.models import User
from app.articles.models import Article, ArticleCategory
from app.articles.utils import video_embed_url


class VideoUrlTest(unittest.TestCase):
    def test_only_known_hosts_become_embeds(self):
        self.assertEqual(video_embed_url('https://www.aparat.com/v/AbC1'),
                         'https://www.aparat.com/video/video/embed/videohash/AbC1/vt/frame')
        self.assertEqual(video_embed_url('https://youtu.be/dQw4w9WgXcQ'),
                         'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
        for bad in ('https://evil.com/v/x', 'javascript:alert(1)', 'http://www.aparat.com/v/x',
                    'https://www.aparat.com.evil.com/v/x', '', None):
            self.assertIsNone(video_embed_url(bad))


class ActivitiesTest(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY='t', WTF_CSRF_ENABLED=False,
                               SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        admin = User(username='adm', email='a@example.com', fullname='adm', role='admin')
        admin.set_password('pass12345')
        admin.is_active = True
        db.session.add(admin)
        db.session.commit()
        self.admin = admin
        with self.client.session_transaction() as s:
            s['_user_id'] = str(admin.id)
            s['_fresh'] = True

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()
        os.environ.pop('DATABASE_URL', None)

    def test_sections_are_separate_and_menu_lists_activity_categories(self):
        db.session.add_all([ArticleCategory(name='ادبی', slug='adabi'),
                            ArticleCategory(name='گزارش', slug='gozaresh', section='activities')])
        db.session.commit()
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('/activities/category/gozaresh', html)
        self.assertIn('/articles/category/adabi', html)
        self.assertNotIn('/articles/category/gozaresh', html)

    def test_create_from_existing_panel_and_public_pages(self):
        cat = ArticleCategory(name='گزارش', slug='gozaresh', section='activities')
        db.session.add(cat)
        db.session.commit()
        r = self.client.post('/admin/articles/new?section=activities', data={
            'title': 'مرحله اول', 'content_html': '<p>متن</p>', 'status': 'published', 'category_id': cat.id,
            'stage_label': 'مرحله ۱', 'contributors': 'علی\nمریم', 'video_url': 'https://www.aparat.com/v/abc123'})
        self.assertEqual(r.status_code, 302)
        a = Article.query.one()
        self.assertEqual((a.section, a.stage_label, a.contributors_list), ('activities', 'مرحله ۱', ['علی', 'مریم']))
        page = self.client.get('/activities/').get_data(as_text=True)
        self.assertIn('مرحله اول', page)
        self.assertNotIn('مرحله اول', self.client.get('/articles/').get_data(as_text=True))   # در مقالات نیست
        detail = self.client.get(f'/activities/{a.slug}').get_data(as_text=True)
        self.assertIn('aparat.com/video/video/embed/videohash/abc123', detail)
        self.assertEqual(self.client.get(f'/articles/{a.slug}').status_code, 302)               # ریدایرکت به وبلاگ
        bad = self.client.post('/admin/articles/new?section=activities', data={
            'title': 'x', 'content_html': 'y', 'status': 'draft', 'video_url': 'https://evil.com/v/1'})
        self.assertEqual(bad.status_code, 200)                                                   # لینک نامعتبر رد شد
        self.assertEqual(Article.query.count(), 1)

    def test_upload_is_converted_to_webp(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (300, 200), 'red').save(buf, 'PNG')
        buf.seek(0)
        folder = self.app.config['ARTICLE_IMAGE_UPLOAD_FOLDER']
        r = self.client.post('/admin/articles/upload-image', data={'file': (buf, 'photo.png')},
                             content_type='multipart/form-data')
        loc = r.get_json()['location']
        self.assertTrue(loc.endswith('.webp'))
        self.assertEqual(Image.open(os.path.join(folder, loc.rsplit('/', 1)[-1])).format, 'WEBP')
        self.assertEqual(self.client.get(loc).mimetype, 'image/webp')


if __name__ == '__main__':
    unittest.main()
