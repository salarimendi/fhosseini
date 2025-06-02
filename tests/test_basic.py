"""
Basic tests for the Ferdowsi Hosseini website
"""
import unittest
import os
import tempfile
from app import create_app, db
from app.models import User, Title, Verse, Comment, Recording

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
        
        # ایجاد جداول پایگاه داده
        with self.app.app_context():
            db.create_all()
        
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
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
        db.drop_all()
        self.app_context.pop()
        
        # حذف متغیر محیطی
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
    
    def test_user_creation(self):
        """Test user creation."""
        user = User(
            username='testuser',
            email='test@example.com',
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
            verse_2='بیت دوم'
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
        user = User(username='researcher', email='res@test.com', role='researcher')
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
        user = User(username='reader', email='reader@test.com', role='reader')
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
        self.assertEqual(recording.file_path, 'static/uploads/test_recording.mp3')
        self.assertFalse(recording.is_approved)
    
    def test_user_roles_and_permissions(self):
        """Test user roles and permissions."""
        # Test admin user
        admin = User(username='admin2', email='admin2@test.com', role='admin')
        admin.set_password('password')
        
        # Test researcher user
        researcher = User(username='researcher', email='researcher@test.com', role='researcher')
        researcher.set_password('password')
        
        # Test reader user
        reader = User(username='reader', email='reader@test.com', role='reader')
        reader.set_password('password')
        
        # Test regular user
        user = User(username='user', email='user@test.com', role='user')
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