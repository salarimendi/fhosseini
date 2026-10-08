"""
Basic tests for the Ferdowsi Hosseini website
"""
import unittest
import os
import tempfile
import uuid
from app import create_app, db
from app.models import User, Title, Verse, Comment, Recording, Version
from app.utils.database import get_version_positions_for_title

class TestConfig:
    """Test configuration class."""
    TESTING = True
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class BasicTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # استفاده از پایگاه داده در حافظه برای سرعت و سادگی بیشتر
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        # ایجاد اپلیکیشن با تنظیمات تست
        self.app = create_app()
        
        # اعمال تنظیمات تست
        self.app.config.from_object(TestConfig)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # ایجاد context و client
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.client = self.app.test_client()
        self._profile_test_user_ids = set()
        
        # ایجاد جداول پایگاه داده
        with self.app.app_context():
            db.create_all()
        
    def tearDown(self):
        """Clean up after each test method."""
        for user_id in self._profile_test_user_ids:
            user = db.session.get(User, user_id)
            if user:
                db.session.delete(user)
        if self._profile_test_user_ids:
            db.session.commit()
        db.session.remove()
        self.app_context.pop()

        # حذف متغیر محیطی
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_app_exists(self):
        """Test that the app exists."""
        self.assertIsNotNone(self.app)
    
    def test_app_is_testing(self):
        """Test that the app is in testing mode."""
        self.assertTrue(self.app.config['TESTING'])
    
    def test_index_page(self):
        """Test that the index page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('فردوسی حسینی', response.get_data(as_text=True))
    
    def test_login_page(self):
        """Test that the login page loads."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('ورود', response.get_data(as_text=True))
    
    def test_register_page(self):
        """Test that the register page loads."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn('ثبت نام', response.get_data(as_text=True))

    def _create_authenticated_user(self):
        test_id = uuid.uuid4().hex
        user = User(
            username=f'profile_{test_id}',
            email=f'profile-{test_id}@example.com',
            fullname='Profile User',
            role='user',
            is_active=True
        )
        user.set_password('original-password')
        db.session.add(user)
        db.session.commit()
        self._profile_test_user_ids.add(user.id)
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True
        return user

    def test_profile_edit_updates_only_fullname_and_email(self):
        user = self._create_authenticated_user()
        original_username = user.username
        updated_email = f'updated-{uuid.uuid4().hex}@example.com'

        menu_response = self.client.get('/')
        self.assertIn('ویرایش مشخصات', menu_response.get_data(as_text=True))

        response = self.client.post('/auth/edit_profile', data={
            'fullname': 'Updated Name',
            'email': updated_email.upper()
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.fullname, 'Updated Name')
        self.assertEqual(user.email, updated_email)
        self.assertEqual(user.username, original_username)
        self.assertTrue(user.check_password('original-password'))

    def test_profile_edit_rejects_duplicate_email_and_long_fullname(self):
        user = self._create_authenticated_user()
        original_email = user.email
        other_test_id = uuid.uuid4().hex
        other_user = User(
            username=f'other_{other_test_id}',
            email=f'other-{other_test_id}@example.com',
            fullname='Other User'
        )
        other_user.set_password('other-password')
        db.session.add(other_user)
        db.session.commit()
        self._profile_test_user_ids.add(other_user.id)

        duplicate_email_response = self.client.post('/auth/edit_profile', data={
            'fullname': 'New Name',
            'email': other_user.email.upper()
        })
        self.assertEqual(duplicate_email_response.status_code, 200)
        self.assertIn('این ایمیل قبلاً ثبت شده است.', duplicate_email_response.get_data(as_text=True))
        self.assertEqual(user.email, original_email)

        long_name_response = self.client.post('/auth/edit_profile', data={
            'fullname': 'ن' * 41,
            'email': 'profile@example.com'
        })
        self.assertEqual(long_name_response.status_code, 200)
        self.assertIn('۴۰ کاراکتر', long_name_response.get_data(as_text=True))
        self.assertEqual(user.fullname, 'Profile User')

class ModelTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # استفاده از پایگاه داده در حافظه
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        self.app = create_app()
        
        # اعمال تنظیمات تست
        self.app.config.from_object(TestConfig)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # ایجاد جداول پایگاه داده
        with self.app.app_context():
            db.create_all()
        
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        self.app_context.pop()

        # حذف متغیر محیطی
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_user_creation(self):
        """Test user creation."""
        user = User(
            username='testuser',
            email='test@example.com',
            fullname='Test User',
            role='researcher'
        )
        user.set_password('testpassword')
        
        db.session.add(user)
        db.session.commit()
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'researcher')
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertTrue(user.can_comment())
        self.assertFalse(user.can_record())
        self.assertFalse(user.is_admin())
    
    def test_title_creation(self):
        """Test title creation."""
        title = Title(
            title='تست شعر',
            garden=1,
            order_in_garden=1
        )
        
        db.session.add(title)
        db.session.commit()
        
        self.assertEqual(title.title, 'تست شعر')
        self.assertEqual(title.garden, 1)
        self.assertEqual(title.order_in_garden, 1)
        self.assertEqual(title.garden_name, 'خیابان اول باغ فردوس')

    def test_cumulative_version_positions_ignore_subtitles(self):
        previous_title = Title(title='شعر پیشین', garden=1, order_in_garden=1)
        current_title = Title(title='شعر جاری', garden=1, order_in_garden=2)
        db.session.add_all([previous_title, current_title])
        db.session.flush()

        db.session.add_all([
            Verse(title_id=previous_title.id, order_in_title=1, verse_1='بیت ۱', verse_1_tag='بیت ۱', variant_diff='', present_in_versions='کا، اد'),
            Verse(title_id=previous_title.id, order_in_title=2, verse_1='بیت ۲', verse_1_tag='بیت ۲', variant_diff='', present_in_versions='کا'),
            Version(name='کا', sort_order=1),
            Version(name='اد', sort_order=2),
        ])
        db.session.flush()

        current_first = Verse(
            title_id=current_title.id,
            order_in_title=1,
            verse_1='بیت جاری ۱',
            verse_1_tag='بیت جاری ۱',
            variant_diff='',
            present_in_versions='اد، کا',
        )
        subtitle = Verse(
            title_id=current_title.id,
            order_in_title=2,
            verse_1='زیرعنوان',
            verse_1_tag='زیرعنوان',
            variant_diff='',
            present_in_versions='کا، اد',
            is_subtitle=1,
        )
        current_second = Verse(
            title_id=current_title.id,
            order_in_title=3,
            verse_1='بیت جاری ۲',
            verse_1_tag='بیت جاری ۲',
            variant_diff='',
            present_in_versions='کا',
        )
        db.session.add_all([current_first, subtitle, current_second])
        db.session.flush()

        _, positions = get_version_positions_for_title(
            current_title,
            [current_first, subtitle, current_second],
        )

        self.assertEqual(positions[current_first.id], [('کا', 3), ('اد', 2)])
        self.assertEqual(positions[subtitle.id], [])
        self.assertEqual(positions[current_second.id], [('کا', 4)])
    
    def test_verse_creation(self):
        """Test verse creation."""
        # First create a title
        title = Title(
            title='تست شعر',
            garden=1,
            order_in_garden=1
        )
        db.session.add(title)
        db.session.commit()
        
        # Then create a verse
        verse = Verse(
            title_id=title.id,
            order_in_title=1,
            verse_1='بیت اول',
            verse_2='بیت دوم',
            verse_1_tag='بیت اول',
            verse_2_tag='بیت دوم'
        )
        
        db.session.add(verse)
        db.session.commit()
        
        self.assertEqual(verse.verse_1, 'بیت اول')
        self.assertEqual(verse.verse_2, 'بیت دوم')
        self.assertEqual(verse.title_id, title.id)
        self.assertEqual(verse.full_verse, 'بیت اول *** بیت دوم')
    
    def test_comment_creation(self):
        """Test comment creation."""
        # Create user and title first
        user = User(username='researcher', email='res@test.com', fullname='Researcher User', role='researcher')
        user.set_password('password')
        db.session.add(user)
        
        title = Title(title='شعر تست', garden=1, order_in_garden=1)
        db.session.add(title)
        db.session.commit()
        
        # Create comment
        comment = Comment(
            user_id=user.id,
            title_id=title.id,
            comment='این یک نظر تست است'
        )
        db.session.add(comment)
        db.session.commit()
        
        self.assertEqual(comment.comment, 'این یک نظر تست است')
        self.assertEqual(comment.user_id, user.id)
        self.assertEqual(comment.title_id, title.id)
        self.assertFalse(comment.is_approved)
    
    def test_recording_creation(self):
        """Test recording creation."""
        # Create user and title first
        user = User(username='reader', email='reader@test.com', fullname='Reader User', role='reader')
        user.set_password('password')
        db.session.add(user)
        
        title = Title(title='شعر تست', garden=1, order_in_garden=1)
        db.session.add(title)
        db.session.commit()
        
        # Create recording
        recording = Recording(
            user_id=user.id,
            title_id=title.id,
            filename='test_recording.mp3',
            original_filename='my_recording.mp3',
            file_size=1024000,  # 1MB
            duration=60.5
        )
        db.session.add(recording)
        db.session.commit()
        
        self.assertEqual(recording.filename, 'test_recording.mp3')
        self.assertEqual(recording.original_filename, 'my_recording.mp3')
        self.assertEqual(recording.file_size, 1024000)
        self.assertEqual(recording.duration, 60.5)
        self.assertEqual(recording.file_size_mb, 0.98)  # rounded
        expected_path = os.path.join(
            self.app.config['UPLOAD_FOLDER'],
            'test_recording.mp3'
        )
        self.assertEqual(
            os.path.normpath(recording.file_path),
            os.path.normpath(expected_path)
        )
        self.assertFalse(recording.is_approved)
    
    def test_user_roles_and_permissions(self):
        """Test user roles and permissions."""
        # Test admin user
        admin = User(username='admin2', email='admin2@test.com', fullname='Admin User', role='admin')
        admin.set_password('password')
        
        # Test researcher user
        researcher = User(username='researcher', email='researcher@test.com', fullname='Researcher User', role='researcher')
        researcher.set_password('password')
        
        # Test reader user
        reader = User(username='reader', email='reader@test.com', fullname='Reader User', role='reader')
        reader.set_password('password')
        
        # Test regular user
        user = User(username='user', email='user@test.com', fullname='Regular User', role='user')
        user.set_password('password')
        
        db.session.add_all([admin, researcher, reader, user])
        db.session.commit()
        
        # Test admin permissions
        self.assertTrue(admin.is_admin())
        self.assertTrue(admin.can_comment())
        self.assertTrue(admin.can_record())
        self.assertTrue(admin.has_role('admin'))
        
        # Test researcher permissions
        self.assertFalse(researcher.is_admin())
        self.assertTrue(researcher.can_comment())
        self.assertFalse(researcher.can_record())
        self.assertTrue(researcher.has_role('researcher'))
        
        # Test reader permissions
        self.assertFalse(reader.is_admin())
        self.assertFalse(reader.can_comment())
        self.assertTrue(reader.can_record())
        self.assertTrue(reader.has_role('reader'))
        
        # Test regular user permissions
        self.assertFalse(user.is_admin())
        self.assertFalse(user.can_comment())
        self.assertFalse(user.can_record())
        self.assertTrue(user.has_role('user'))

if __name__ == '__main__':
    unittest.main()