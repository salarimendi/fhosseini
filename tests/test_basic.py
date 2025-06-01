"""
Basic tests for the Ferdowsi Hosseini website
"""
import unittest
import os
import tempfile
from app import create_app, db
from app.models import User, Title, Verse

class BasicTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create app with testing configuration
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False
        })
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.client = self.app.test_client()
        
        # Create database tables
        db.create_all()
        
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        
        self.app_context.pop()
        
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
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
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{self.db_path}',
            'SECRET_KEY': 'test-secret-key'
        })
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        
        self.app_context.pop()
        
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
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
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.check_password('wrongpassword'))
    
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

if __name__ == '__main__':
    unittest.main()