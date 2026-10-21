"""
تست‌های هدفمند: شمارنده‌های داشبورد، حذف کاربر، بازگشت با فیلتر در مدیریت نظرات،
ناوبری تیتر قبلی/بعدی و برچسب «سایر منابع بررسی‌شده» در فرم پژوهشی.
"""
import json
import os
import unittest
from urllib.parse import urlsplit, parse_qs

from app import create_app, db
from app.models import User, Title, Verse, Comment, Recording, VerseCorrection
from app.utils.database import (
    get_admin_dashboard_counts, get_adjacent_titles, safe_internal_path,
)
from app.routes.admin import comments_filter_args, safe_comments_return_url


class _Base(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY='test', WTF_CSRF_ENABLED=False,
                               SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.ctx.pop()
        os.environ.pop('DATABASE_URL', None)

    # --- کمکی‌ها ---
    def user(self, name, role='researcher'):
        u = User(username=name, email=f'{name}@example.com', fullname=name, role=role)
        u.set_password('pass12345')
        u.is_active = True
        db.session.add(u)
        db.session.commit()
        return u

    def login(self, user):
        with self.client.session_transaction() as s:
            s['_user_id'] = str(user.id)
            s['_fresh'] = True

    def title(self, garden, order, text='t'):
        t = Title(title=f'{text}{garden}-{order}', garden=garden, order_in_garden=order)
        db.session.add(t)
        db.session.commit()
        return t

    def research_comment(self, user, title, status='approved', reviewed='منبع قدیمی'):
        data = {'form_type': 'research_form',
                'subtopics': [{'title': 'x', 'reviewed_sources': reviewed}]}
        c = Comment(user_id=user.id, title_id=title.id,
                    comment=json.dumps(data, ensure_ascii=False), status=status)
        db.session.add(c)
        db.session.commit()
        return c


class DashboardCountsTest(_Base):
    def test_empty_database(self):
        c = get_admin_dashboard_counts()
        self.assertEqual((c['pending_comments'], c['pending_corrections'],
                          c['approved_corrections'], c['comments']), (0, 0, 0, 0))

    def test_counters_are_separate(self):
        admin, r = self.user('adm', 'admin'), self.user('res')
        t = self.title(1, 1)
        v = Verse(title_id=t.id, order_in_title=1, verse_1='a', verse_1_tag='a')
        db.session.add(v)
        db.session.commit()
        for st in ('approved', 'pending', 'pending', 'rejected'):
            self.research_comment(r, t, status=st)
        for approved in (True, True, True, False):
            db.session.add(VerseCorrection(verse_id=v.id, field_name='verse_1', new_text='n',
                                           created_by=r.id, is_approved=approved))
        db.session.commit()
        c = get_admin_dashboard_counts()
        self.assertEqual(c['comments'], 4)              # کل نظرهای پژوهشی
        self.assertEqual(c['pending_comments'], 2)      # فقط Comment.status == pending
        self.assertEqual(c['approved_corrections'], 3)  # فقط VerseCorrection.is_approved
        self.assertEqual(c['pending_corrections'], 1)

    def test_dashboard_page_labels(self):
        self.login(self.user('adm', 'admin'))
        page = self.client.get('/admin/').get_data(as_text=True)
        for label in ('اصلاحات ابیات در انتظار تأیید', 'مجموع اصلاحات ابیات تأییدشده',
                      'نظرهای پژوهشی در انتظار تأیید', 'کل نظرهای پژوهشی'):
            self.assertIn(label, page)


class DeleteUserTest(_Base):
    def test_requires_admin_and_post(self):
        victim = self.user('victim')
        self.login(self.user('res2'))
        self.assertNotEqual(self.client.post(f'/admin/users/{victim.id}/delete').status_code, 200)
        self.login(self.user('adm', 'admin'))
        self.assertEqual(self.client.get(f'/admin/users/{victim.id}/delete').status_code, 405)

    def test_self_admin_and_dependents_are_protected(self):
        admin = self.user('adm', 'admin')
        other_admin = self.user('adm2', 'admin')
        busy = self.user('busy')
        self.research_comment(busy, self.title(1, 1))
        self.login(admin)
        for uid, code in ((admin.id, 400), (other_admin.id, 400), (busy.id, 409)):
            r = self.client.post(f'/admin/users/{uid}/delete')
            self.assertEqual(r.status_code, code)
            self.assertFalse(r.get_json()['success'])
        self.assertIsNotNone(db.session.get(User, busy.id))
        self.assertEqual(Comment.query.count(), 1)

    def test_empty_account_can_be_deleted(self):
        self.login(self.user('adm', 'admin'))
        empty = self.user('empty')
        r = self.client.post(f'/admin/users/{empty.id}/delete')
        self.assertTrue(r.get_json()['success'])
        self.assertIsNone(db.session.get(User, empty.id))


class CommentFiltersReturnTest(_Base):
    def test_filter_whitelist(self):
        out = comments_filter_args({'search': ' ab ', 'researcher': '3', 'status': 'pending',
                                    'garden': 'x', 'order': '7', 'page': '3', 'evil': '1'})
        self.assertEqual(out, {'search': 'ab', 'researcher': '3', 'status': 'pending',
                              'order': '7', 'page': 3})
        self.assertNotIn('status', comments_filter_args({'status': 'hacked'}))

    def test_safe_internal_path(self):
        for bad in ('http://evil.com', '//evil.com', 'javascript:alert(1)', '/\\evil', None, '', 'x/y'):
            self.assertEqual(safe_internal_path(bad, '/d'), '/d')
        self.assertEqual(safe_internal_path('/admin/comments?a=1', '/d'), '/admin/comments?a=1')

    def test_return_url_rebuilt_only_for_comments_list(self):
        with self.app.test_request_context():
            self.assertEqual(safe_comments_return_url('http://evil.com/x'), '/admin/comments')
            self.assertEqual(safe_comments_return_url('/admin/users?status=pending'), '/admin/comments')
            url = safe_comments_return_url('/admin/comments?status=pending&page=2&x=1&garden=2')
            q = parse_qs(urlsplit(url).query)
            self.assertEqual(q, {'status': ['pending'], 'page': ['2'], 'garden': ['2']})

    def test_edit_link_and_page_carry_filters(self):
        admin, r = self.user('adm', 'admin'), self.user('res')
        t = self.title(2, 5)
        c = self.research_comment(r, t, status='pending')
        self.login(admin)
        listing = self.client.get('/admin/comments?status=pending&garden=2').get_data(as_text=True)
        self.assertIn(f'/admin/comments/{c.id}/research-edit?', listing)
        page = self.client.get(f'/admin/comments/{c.id}/research-edit?status=pending&garden=2&evil=1')
        html = page.get_data(as_text=True)
        self.assertEqual(page.status_code, 200)
        self.assertIn('/admin/comments?status=pending&amp;garden=2', html)
        self.assertNotIn('evil', html)


class PrevNextTest(_Base):
    def test_adjacent_titles_stay_in_garden(self):
        a1, a3, a7 = self.title(1, 1), self.title(1, 3), self.title(1, 7)
        b2 = self.title(2, 2)
        self.assertEqual(get_adjacent_titles(a3), (a1, a7))
        self.assertEqual(get_adjacent_titles(a1)[0], None)   # ابتدای باغ: قبلی ندارد
        self.assertEqual(get_adjacent_titles(a7)[1], None)   # انتهای باغ: بعدی ندارد
        self.assertEqual(get_adjacent_titles(b2), (None, None))

    def test_researcher_form_nav_and_labels(self):
        r = self.user('res')
        t1, t2, t3 = self.title(1, 1), self.title(1, 2), self.title(1, 3)
        self.login(r)
        mid = self.client.get(f'/verses/get_research_form?title_id={t2.id}').get_data(as_text=True)
        self.assertIn('تیتر قبلی', mid)
        self.assertIn('تیتر بعدی', mid)
        self.assertIn('رفتن به شعر', mid)
        self.assertNotIn('بازگشت به شعر', mid)
        self.assertIn('سایر منابع بررسی‌شده', mid)
        first = self.client.get(f'/verses/get_research_form?title_id={t1.id}').get_data(as_text=True)
        self.assertIn('اولین تیتر این باغ', first)

    def test_view_only_uses_approved_and_old_data_preserved(self):
        r = self.user('res')
        t1, t2 = self.title(1, 1), self.title(1, 2)
        prev_c = self.research_comment(r, t1, status='approved')
        cur = self.research_comment(r, t2, status='approved', reviewed='متن قدیمی بدون تغییر')
        html = self.client.get(f'/verses/view_research_comment/{cur.id}').get_data(as_text=True)
        self.assertIn(f'/verses/view_research_comment/{prev_c.id}', html)   # تنها نظر تأییدشده‌ی قبلی
        self.assertIn('متن قدیمی بدون تغییر', html)                        # کلید reviewed_sources حفظ شده
        self.assertIn('آخرین تیتر این باغ', html)
        self.assertIn('سایر منابع بررسی‌شده', html)

    def test_admin_form_prev_options_and_disabled(self):
        admin, r1, r2 = self.user('adm', 'admin'), self.user('r1'), self.user('r2')
        t1, t2, t3 = self.title(1, 1), self.title(1, 2), self.title(1, 3)
        self.research_comment(r1, t1)
        self.research_comment(r2, t1)            # دو نظر برای تیتر قبلی → منوی چندگزینه‌ای
        cur = self.research_comment(r1, t2)
        self.login(admin)
        html = self.client.get(f'/admin/comments/{cur.id}/research-edit').get_data(as_text=True)
        self.assertIn('research-title-meta__menu', html)
        self.assertIn('برای تیتر بعدی نظر پژوهشی ثبت نشده', html)   # t3 نظری ندارد


class FontAndMenuTest(_Base):
    def test_poem_font_default_and_admin_setting(self):
        from app.utils.database import get_poem_font_default, set_poem_font_default
        self.assertEqual(get_poem_font_default(), 'vazir')
        self.login(self.user('adm', 'admin'))
        self.client.post('/admin/settings', data={'poem_font': 'alavi'})
        self.assertEqual(get_poem_font_default(), 'alavi')
        self.client.post('/admin/settings', data={'poem_font': 'bogus'})
        self.assertEqual(get_poem_font_default(), 'alavi')       # مقدار نامعتبر رد می‌شود
        self.assertIn('data-poem-font="alavi"', self.client.get('/').get_data(as_text=True))
        self.client.get('/auth/logout')
        self.login(self.user('res'))
        self.assertNotEqual(self.client.post('/admin/settings', data={'poem_font': 'sahel'}).status_code, 200)
        self.assertEqual(get_poem_font_default(), 'alavi')

    def test_nav_lists_categories_automatically(self):
        from app.articles.models import ArticleCategory
        home = self.client.get('/').get_data(as_text=True)
        self.assertNotIn('/articles/category/', home)             # بدون دسته‌بندی: منو بدون خطا
        db.session.add(ArticleCategory(name='ادبی‌تست', slug='adabi-test'))
        db.session.commit()
        self.assertIn('ادبی‌تست', self.client.get('/').get_data(as_text=True))
        ArticleCategory.query.delete()
        db.session.commit()
        self.assertNotIn('ادبی‌تست', self.client.get('/').get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
