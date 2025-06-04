#!/bin/bash

# رنگ‌ها برای نمایش بهتر پیام‌ها
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# تابع نمایش پیام‌ها
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# دریافت مسیر نصب
read -p "لطفاً مسیر نصب برنامه را وارد کنید (مثال: ~/public_html/myapp): " PROJECT_PATH
read -p "لطفاً پورت اختصاص داده شده توسط هاست را وارد کنید: " PORT_NUMBER

# ایجاد ساختار پوشه‌ها
print_message "در حال ایجاد ساختار پوشه‌ها..."
mkdir -p $PROJECT_PATH
cd $PROJECT_PATH

# استخراج فایل‌های پروژه
print_message "در حال استخراج فایل‌های پروژه..."
if [ -f "ferdowsi_website.zip" ]; then
    unzip ferdowsi_website.zip
else
    print_warning "فایل ferdowsi_website.zip یافت نشد!"
    print_warning "لطفاً فایل را در مسیر $PROJECT_PATH قرار دهید و دوباره اسکریپت را اجرا کنید."
    exit 1
fi

# ایجاد محیط مجازی Python
print_message "در حال ایجاد محیط مجازی Python..."
python3 -m venv venv
source venv/bin/activate

# نصب وابستگی‌ها
print_message "در حال نصب وابستگی‌ها..."
pip install --user -r requirements.txt

# ایجاد فایل پیکربندی برنامه
print_message "در حال ایجاد فایل پیکربندی..."
cat > $PROJECT_PATH/config.py << EOL
import os

class Config:
    SECRET_KEY = os.urandom(32)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'ferdosi.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
EOL

# ایجاد فایل اجرایی
print_message "در حال ایجاد فایل اجرایی..."
cat > $PROJECT_PATH/run.py << EOL
#!/usr/bin/env python3
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', ${PORT_NUMBER}))
    app.run(host='0.0.0.0', port=port)
EOL

chmod +x $PROJECT_PATH/run.py

# ایجاد فایل supervisor (اگر هاست از supervisor پشتیبانی می‌کند)
mkdir -p ~/.supervisor/conf.d/
cat > ~/.supervisor/conf.d/myapp.conf << EOL
[program:myapp]
command=$PROJECT_PATH/venv/bin/python $PROJECT_PATH/run.py
directory=$PROJECT_PATH
autostart=true
autorestart=true
stderr_logfile=$PROJECT_PATH/logs/err.log
stdout_logfile=$PROJECT_PATH/logs/out.log
environment=PATH="$PROJECT_PATH/venv/bin"
EOL

# ایجاد پوشه‌های مورد نیاز
mkdir -p $PROJECT_PATH/logs
mkdir -p $PROJECT_PATH/instance
mkdir -p $PROJECT_PATH/app/static/uploads

# تنظیم مجوزها
print_message "در حال تنظیم مجوزها..."
chmod -R 755 $PROJECT_PATH
chmod 660 $PROJECT_PATH/instance/ferdosi.db
chmod -R 775 $PROJECT_PATH/app/static/uploads

# ایجاد فایل htaccess برای Apache (اگر هاست از Apache استفاده می‌کند)
cat > $PROJECT_PATH/.htaccess << EOL
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ run.py [QSA,L]
EOL

print_message "نصب و راه‌اندازی با موفقیت انجام شد!"
print_message "برای اجرای برنامه، دستورات زیر را اجرا کنید:"
echo "cd $PROJECT_PATH"
echo "source venv/bin/activate"
echo "python run.py"
print_message "برنامه شما روی پورت $PORT_NUMBER در حال اجرا خواهد بود."
print_message "لاگ‌های برنامه در پوشه $PROJECT_PATH/logs ذخیره می‌شوند."

# راهنمایی‌های نهایی
cat << EOL

راهنمای مهم:
1. اطمینان حاصل کنید که پورت $PORT_NUMBER توسط هاست به شما اختصاص داده شده است.
2. در صورت نیاز به راه‌اندازی مجدد برنامه:
   - وارد پوشه $PROJECT_PATH شوید
   - محیط مجازی را با دستور 'source venv/bin/activate' فعال کنید
   - برنامه را با دستور 'python run.py' اجرا کنید
3. برای اجرای دائمی برنامه، از سرویس supervisor هاست استفاده کنید (در صورت وجود)
4. تنظیمات دیتابیس و مسیرها در فایل config.py قابل ویرایش هستند
5. لاگ‌های برنامه در پوشه logs قابل مشاهده هستند

EOL