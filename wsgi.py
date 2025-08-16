import sys
import os

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from ssl_config import SSLConfig

application = create_app()

# فعال‌سازی تنظیمات SSL فقط اگر متغیر محیطی ENABLE_SSL تنظیم شده باشد
if os.environ.get('ENABLE_SSL') == 'true':
    SSLConfig.init_app(application)
    SSLConfig.configure_proxy(application)

if __name__ == '__main__':
    application.run() 