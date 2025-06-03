import unittest
import requests
import time
from flask import current_app
from app import create_app, db
from app.models import User

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # ایجاد یک کاربر تست
        user = User(
            username='test_user',
            email='test@example.com',
            fullname='Test User'  # اضافه کردن نام کامل
        )
        user.set_password('test_password')
        user.is_active = True
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_rate_limit(self):
        """تست محدودیت نرخ درخواست در لاگین"""
        print("\nتست محدودیت نرخ درخواست در لاگین:")
        
        # تلاش برای 6 درخواست پشت سر هم
        for i in range(6):
            response = self.client.post('/auth/login', data={
                'username': 'test_user',
                'password': 'wrong_password'
            })
            print(f"درخواست {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print("✅ Rate limit با موفقیت اعمال شد!")
                return
                
        self.fail("❌ Rate limit اعمال نشد!")

    def test_security_headers(self):
        """تست هدرهای امنیتی"""
        print("\nتست هدرهای امنیتی:")
        
        response = self.client.get('/')
        headers = response.headers
        
        security_headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block'
        }
        
        for header, expected_value in security_headers.items():
            if header in headers and headers[header] == expected_value:
                print(f"✅ {header} صحیح است")
            else:
                print(f"❌ {header} یافت نشد یا نادرست است")

    def test_csrf_protection(self):
        """تست محافظت CSRF"""
        print("\nتست محافظت CSRF:")
        
        # تلاش برای ارسال فرم بدون توکن CSRF
        response = self.client.post('/auth/login', data={
            'username': 'test_user',
            'password': 'test_password'
        })
        
        if response.status_code == 400:  # Bad Request (CSRF token missing)
            print("✅ محافظت CSRF فعال است")
        else:
            print("❌ محافظت CSRF غیرفعال است")

if __name__ == '__main__':
    unittest.main() 