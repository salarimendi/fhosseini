# سایت فردوسی حسینی

سایت پژوهشی-تحقیقی برای کتاب شعر "چهار خیابان باغ فردوس" از حکیم میرزا احمد الهامی کرمانشاهی

## ویژگی‌های اصلی

- نمایش اشعار به تفکیک باغ‌ها (فصل‌ها)
- جستجو در تیترها و ابیات
- سیستم کاربری با نقش‌های مختلف (مدیر، محقق، خواننده، کاربر عادی)
- امکان ثبت نظرات پژوهشی توسط محققان
- امکان ثبت نظرات تصحیحی روی ابیات توسط کاربران مجاز
- ضبط و پخش صوتی اشعار توسط خوانندگان
- پنل مدیریت کامل با امکان تایید نظرات و اصلاحات

## نقش‌های کاربری

1. **کاربر عادی**: مشاهده سایت و پخش فایل‌های صوتی
2. **محقق**: ثبت نظرات پژوهشی
3. **خواننده**: ضبط و بارگذاری فایل‌های صوتی
4. **مدیر**: دسترسی کامل و مدیریت کاربران، تایید نظرات و اصلاحات ابیات
5. **کاربران مجاز تصحیح**: ثبت اصلاحات روی ابیات (تصحیح متنی، اعراب، نگارش و نسخه‌ها)

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.8+
- pip

### مراحل نصب

1. کلون کردن پروژه:
```bash
git clone https://github.com/salarimendi/fhosseini.git
cd fhosseini
```

2. ایجاد محیط مجازی:
```bash
python -m venv venv
```

3. فعال‌سازی محیط مجازی:

**در لینوکس/MacOS:**
```bash
source venv/bin/activate
```

**در ویندوز:**
```bash
venv\Scripts\activate
```

4. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

5. تنظیمات محیطی:

**برای محیط توسعه (Development):**
- نیازی به تنظیم متغیرهای محیطی نیست
- همه تنظیمات با مقادیر پیش‌فرض در `config.py` تعریف شده‌اند
- برنامه به صورت خودکار در حالت development اجرا می‌شود

**برای محیط تولید (Production):**
متغیرهای محیطی زیر باید در سرور تنظیم شوند:
```bash
# تنظیمات امنیتی
SECRET_KEY=your_secret_key_here
WTF_CSRF_SECRET_KEY=your_csrf_secret_key

# تنظیمات پایگاه داده
DATABASE_URL=your_database_url

# تنظیمات ایمیل
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

# تنظیمات سایت
SITE_URL=https://ferdowsihosseini.ir
UPLOAD_FOLDER=/path/to/upload/folder
```

6. راه‌اندازی پایگاه داده:
```bash
python run.py
```

---

## ساختار پروژه

```
fardosi_hosseini/
├── app/
│   ├── __init__.py                 # اعداد اولیه اپلیکیشن
│   ├── models.py                   # مدل‌های پایگاه داده
│   ├── routes/                     # مسیرهای مختلف
│   │   ├── __init__.py
│   │   ├── auth.py                 # احراز هویت
│   │   ├── main.py                 # صفحه اصلی
│   │   ├── verses.py               # اشعار
│   │   ├── admin.py                # پنل مدیریت
│   │   └── comments.py             # نظرات
│   ├── templates/                  # قالب‌های HTML
│   ├── static/                     # فایل‌های استاتیک
│   └── utils/                      # ابزارهای کمکی
├── instance/
│   └── ferdosi.db                  # پایگاه داده SQLite
├── config.py                       # تنظیمات
├── run.py                          # فایل اجرا
└── requirements.txt                # وابستگی‌ها
```

---

## استفاده

1. اجرای سرور:
```bash
python run.py
```

2. باز کردن مرورگر و رفتن به آدرس:
```
http://localhost:5000
```

---

## پیکربندی ایمیل

برای استفاده از قابلیت بازیابی رمز عبور در محیط توسعه، تنظیمات پیش‌فرض در `config.py` کافی است.

برای محیط تولید، برای استفاده از Gmail:

1. فعال‌سازی Two-Factor Authentication در حساب Gmail
2. ایجاد App Password
3. تنظیم متغیرهای محیطی مربوط به ایمیل در سرور با استفاده از App Password به جای رمز اصلی

---

## ساختار جدول ابیات (Verses)

جدول `verses` حاوی اطلاعات شعری و متنی است:

| فیلد | نوع | توضیح |
|------|------|-------|
| `id` | Integer | شناسه یکتای ابیت |
| `title_id` | Integer | شناسه عنوان شعر |
| `order_in_title` | Integer | ترتیب ابیت در شعر |
| `verse_1` | Text | مصراع اول یا تیتر فرعی |
| `verse_2` | Text | مصراع دوم (اختیاری) |
| `variant_diff` | Text | **اختلاف در نسخه‌ها** - توضیح تفاوت‌های میان نسخ‌های مختلف |
| `present_in_versions` | Text | **موجود در نسخ** - مشخص‌کردن اینکه این ابیت در کدام نسخ‌های متن موجود است |
| `is_subtitle` | Integer | **فیلد کنترلی**: ۱ = تیتر فرعی، ۰ = مصراع عادی یا آخرین مصراع مسمط |
| `verse_1_tag` | Text | مصراع اول با تگ HTML |
| `verse_2_tag` | Text | مصراع دوم با تگ HTML (اختیاری) |

### نکات مهم:
- زمانی که `is_subtitle = 1` باشد، `verse_1` یک تیتر فرعی است
- زمانی که `is_subtitle = 0` و تنها `verse_1` پر باشد و `verse_2` خالی باشد، `verse_1` آخرین مصراع یک مسمط است
- فیلدهای `variant_diff` و `present_in_versions` به صورت متنی و دستی تکمیل می‌شوند
- فیلدهای HTML-tagged (`verse_1_tag` و `verse_2_tag`) برای نمایش بهتر ابیات در سایت استفاده می‌شوند

---

## جدول اصلاحات ابیات (Verse Corrections)

جدول `verse_corrections` برای ثبت **نظرات تصحیحی** روی ابیات است:

| فیلد | نوع | توضیح |
|------|------|-------|
| `id` | Integer | شناسه یکتا |
| `verse_id` | Integer | شناسه بیت مورد تصحیح (ForeignKey به verses.id) |
| `field_name` | String | فیلد تصحیح شده (`verse_1` یا `verse_2`) |
| `old_text` | Text | متن قبلی (اختیاری) |
| `new_text` | Text | متن جدید تصحیح شده |
| `correction_type` | String | نوع تصحیح: `text | variant | vocalization | punctuation | other` |
| `note` | Text | توضیح یا یادداشت تصحیح |
| `created_by` | Integer | شناسه کاربر ثبت‌کننده |
| `created_at` | DateTime | تاریخ ثبت تصحیح |
| `is_approved` | Boolean | وضعیت تایید توسط مدیر |
| `approved_by` | Integer | شناسه مدیر تاییدکننده |
| `approved_at` | DateTime | تاریخ تایید |

### نکات مهم:
- هر تصحیح می‌تواند توسط **کاربران مجاز** ثبت شود
- تایید نهایی توسط **مدیر** انجام می‌شود
- تصحیح‌ها در سایت زیر هر بیت نمایش داده می‌شوند پس از تایید

---

## توسعه

پروژه از ساختار MVC استفاده می‌کند:
- **Model**: `app/models.py`
- **View**: `app/templates/`
- **Controller**: `app/routes/`

### افزودن ویژگی جدید:
1. مدل مورد نیاز را در `models.py` تعریف کنید
2. مسیر جدید را در پوشه `routes` ایجاد کنید
3. قالب HTML مربوطه را در `templates` بسازید

---

## تنظیمات Rate Limiting

پروژه از سیستم Rate Limiting برای جلوگیری از حملات DDoS و محدود کردن درخواست‌های مکرر استفاده می‌کند.

### محیط‌های مختلف

#### 1. محیط توسعه (Development)
- **RATELIMIT_DEFAULT**: `5000 per day;1000 per hour;200 per minute`
- **RATELIMIT_LOGIN**: `100 per minute`
- **هدف**: امکان تست راحت‌تر بدون محدودیت‌های شدید

#### 2. محیط تست (Testing)
- **RATELIMIT_DEFAULT**: `10000 per day;1000 per hour;100 per minute`
- **RATELIMIT_LOGIN**: `100 per minute`
- **هدف**: حداقل محدودیت برای اجرای تست‌ها

#### 3. محیط تولید (Production)
- **RATELIMIT_DEFAULT**: `500 per day;100 per hour;20 per minute`
- **RATELIMIT_LOGIN**: `10 per minute`
- **هدف**: امنیت بالا با محدودیت‌های متعادل

### نحوه تغییر محیط

```bash
# محیط توسعه (پیش‌فرض)
export FLASK_CONFIG=development
python run.py

# محیط تست
export FLASK_CONFIG=testing
python -m pytest

# محیط تولید
export FLASK_CONFIG=production
python run.py
```

### نکات مهم

- در محیط توسعه، محدودیت‌ها کمتر هستند تا تست راحت‌تر باشد
- در محیط تولید، محدودیت‌ها برای امنیت مناسب تنظیم شده‌اند
- اگر پیام "Too Many Requests" دریافت کردید، در محیط development اجرا کنید

---

## لینک‌های مفید

- [صفحه اینستاگرام فردوسی حسینی](https://instagram.com/Ferdowsi_Hosseini)
- [کانال تلگرام فردوسی حسینی](https://t.me/Ferdowsi_Hosseini)

---

## مجوز

این پروژه تحت مجوز کپی‌رایت محفوظ است.

---

© ۱۴۰۳ فردوسی حسینی - تمامی حقوق محفوظ است
