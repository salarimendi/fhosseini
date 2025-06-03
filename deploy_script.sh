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

# بررسی اجرا با دسترسی root
if [ "$EUID" -ne 0 ]; then 
    echo "این اسکریپت باید با دسترسی root اجرا شود!"
    echo "لطفاً با دستور sudo اجرا کنید"
    exit 1
fi

# دریافت نام کاربری
read -p "لطفاً نام کاربری سرور را وارد کنید: " USERNAME
read -p "لطفاً دامنه سایت را وارد کنید (مثال: example.com): " DOMAIN_NAME

# مسیر اصلی پروژه
PROJECT_PATH="/home/$USERNAME/myflaskapp"

print_message "شروع نصب و راه‌اندازی..."

# نصب پکیج‌های مورد نیاز
print_message "در حال نصب پکیج‌های مورد نیاز..."
apt update
apt install -y python3-pip python3-venv nginx redis-server unzip certbot python3-certbot-nginx

# ایجاد پوشه پروژه
print_message "در حال ایجاد پوشه پروژه..."
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
pip install -r requirements.txt
pip install gunicorn

# پیکربندی Nginx
print_message "در حال پیکربندی Nginx..."
if [ -f "nginx.conf" ]; then
    # جایگزینی نام دامنه در فایل nginx.conf
    sed -i "s/yourdomain.com/$DOMAIN_NAME/g" nginx.conf
    cp nginx.conf /etc/nginx/sites-available/myflaskapp
    ln -sf /etc/nginx/sites-available/myflaskapp /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t
    systemctl restart nginx
else
    print_warning "فایل nginx.conf یافت نشد!"
fi

# ایجاد سرویس systemd
print_message "در حال ایجاد سرویس systemd..."
cat > /etc/systemd/system/myflaskapp.service << EOL
[Unit]
Description=Gunicorn instance to serve myflaskapp
After=network.target

[Service]
User=$USERNAME
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$PROJECT_PATH/venv/bin"
ExecStart=$PROJECT_PATH/venv/bin/gunicorn --workers 3 --bind unix:myflaskapp.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOL

# تنظیم مجوزها
print_message "در حال تنظیم مجوزها..."
chown -R $USERNAME:www-data $PROJECT_PATH
chmod -R 755 $PROJECT_PATH
chmod 660 $PROJECT_PATH/instance/ferdosi.db
chmod -R 775 $PROJECT_PATH/app/static/uploads

# راه‌اندازی سرویس‌ها
print_message "در حال راه‌اندازی سرویس‌ها..."
systemctl start redis-server
systemctl enable redis-server
systemctl start myflaskapp
systemctl enable myflaskapp

# نصب SSL
print_message "در حال نصب گواهینامه SSL..."
certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email webmaster@$DOMAIN_NAME

# بررسی وضعیت سرویس‌ها
print_message "در حال بررسی وضعیت سرویس‌ها..."
systemctl status nginx
systemctl status myflaskapp
systemctl status redis-server

print_message "نصب و راه‌اندازی با موفقیت انجام شد!"
print_message "وبسایت شما در آدرس https://$DOMAIN_NAME در دسترس خواهد بود."
print_message "برای مشاهده لاگ‌ها می‌توانید از دستورات زیر استفاده کنید:"
echo "sudo tail -f /var/log/nginx/error.log"
echo "sudo journalctl -u myflaskapp" 