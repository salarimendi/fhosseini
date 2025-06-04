"""
تنظیمات SSL برای سایت فردوسی حسینی
این فایل برای مدیریت جداگانه تنظیمات SSL ایجاد شده است
"""

class SSLConfig:
    """تنظیمات SSL که می‌تواند به صورت اختیاری به برنامه اضافه شود"""
    
    @staticmethod
    def init_app(app):
        # تنظیمات پروکسی برای کار با SSL در cPanel
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        
        # تنظیمات امنیتی برای کوکی‌ها
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['REMEMBER_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['REMEMBER_COOKIE_HTTPONLY'] = True
        
        # تنظیمات پروکسی برای کار با SSL
        app.config['PROXY_FIX'] = {
            'x_for': 1,        # X-Forwarded-For
            'x_proto': 1,      # X-Forwarded-Proto
            'x_host': 1,       # X-Forwarded-Host
            'x_port': 1,       # X-Forwarded-Port
            'x_prefix': 1      # X-Forwarded-Prefix
        }

    @staticmethod
    def configure_proxy(app):
        """پیکربندی ProxyFix برای کار درست با SSL در محیط cPanel"""
        from werkzeug.middleware.proxy_fix import ProxyFix
        
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=1,
            x_proto=1,
            x_host=1,
            x_port=1,
            x_prefix=1
        ) 