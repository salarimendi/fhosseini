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

تنظیمات پروژه از فایل `.env` با استفاده از `python-decouple` خوانده می‌شوند.
برای ساخت فایل تنظیمات محلی از نمونه‌ی موجود استفاده کنید.

**در لینوکس/macOS:**
```bash
cp .env.example .env
```

**در Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

سپس مقدارهای واقعی را در `.env` وارد کنید. حداقل تنظیمات لازم:
```env
FLASK_CONFIG=development
SECRET_KEY=your-secret-key
WTF_CSRF_SECRET_KEY=your-csrf-secret-key
DATABASE_URL=sqlite:///ferdosi.db
```

برای محیط تولید مقدار محیط را تغییر دهید:
```env
FLASK_CONFIG=production
ENABLE_SSL=true
```

در محیط Production حتماً برای `SECRET_KEY` و `WTF_CSRF_SECRET_KEY` مقدارهای تصادفی و امن قرار دهید و اطلاعات ایمیل را نیز تنظیم کنید.

فایل `.env.example` شامل مقدارهای نمونه است و باید در Git قرار بگیرد. فایل `.env` شامل اطلاعات محرمانه است، در `.gitignore` قرار دارد و نباید commit یا push شود.

6. راه‌اندازی پایگاه داده:
```bash
python run.py
```

---

## ساختار پروژه

```
fhosseini/
├── app/                                      # هسته برنامه Flask
│   ├── __init__.py                            # ایجاد و پیکربندی برنامه Flask
│   ├── forms.py                               # فرم‌ها و اعتبارسنجی ورودی‌ها
│   ├── models.py                              # مدل‌های پایگاه داده و روابط آن‌ها
│   ├── articles/                               # ماژول مستقل مقالات و وبلاگ
│   │   ├── __init__.py                         # ثبت ماژول با register_articles(app)
│   │   ├── models.py                            # مدل‌های Article و ArticleCategory
│   │   ├── forms.py                             # فرم‌های ArticleForm و ArticleCategoryForm
│   │   ├── utils.py                             # ساخت slug فارسی و پاکسازی HTML
│   │   ├── routes_public.py                     # بلوپرینت عمومی مقالات (/articles/...)
│   │   ├── routes_admin.py                      # بلوپرینت مدیریت مقالات (/admin/articles/...)
│   │   ├── templates/articles/                  # قالب‌های اختصاصی ماژول مقالات
│   │   │   ├── admin/                           # قالب‌های بخش مدیریت مقالات
│   │   │   │   ├── editor.html                  # ویرایشگر مقاله
│   │   │   │   ├── list.html                    # فهرست مقالات در پنل مدیریت
│   │   │   │   └── categories.html              # مدیریت دسته‌بندی‌های مقالات
│   │   │   └── public/                          # قالب‌های عمومی مقالات
│   │   │       ├── list.html                    # فهرست مقالات منتشرشده
│   │   │       └── detail.html                  # جزئیات یک مقاله
│   │   └── static/                              # فایل‌های استاتیک اختصاصی مقالات
│   │       ├── js/article-editor.js             # راه‌اندازی و تعامل ویرایشگر مقاله
│   │       └── vendor/tinymce/                  # فایل‌های TinyMCE خودمیزبان
│   ├── routes/                                # مسیرها و نماهای برنامه
│   │   ├── __init__.py                        # مقداردهی اولیه بسته مسیرها
│   │   ├── admin.py                           # مسیرهای پنل مدیریت
│   │   ├── auth.py                            # ثبت‌نام، ورود و حساب کاربری
│   │   ├── comments.py                        # ثبت و مدیریت نظرات
│   │   ├── main.py                            # صفحات اصلی و عمومی سایت
│   │   ├── verses.py                          # نمایش اشعار و نسخه‌ها
│   │   └── word_398.py                        # قابلیت‌های واژه ۳۹۸
│   ├── utils/                                 # توابع و سرویس‌های کمکی
│   │   ├── audio.py                            # مدیریت فایل‌های صوتی
│   │   ├── database.py                         # عملیات کمکی پایگاه داده
│   │   ├── versioning.py                       # مدیریت نسخه‌های متون
│   │   └── visits.py                            # ثبت و پردازش بازدیدها
│   ├── templates/                              # قالب‌های HTML رابط کاربری
│   │   ├── base.html                            # قالب پایه مشترک صفحات
│   │   ├── home.html                            # صفحه اصلی
│   │   ├── articles.html                        # فهرست مقالات
│   │   ├── biography.html                       # زندگی‌نامه
│   │   ├── contact.html                         # تماس با ما
│   │   ├── documentation.html                   # مستندات سایت
│   │   ├── garden.html                          # نمایش باغ‌ها و فصل‌های شعر
│   │   ├── ilhami_manuscript_studies.html       # مطالعات نسخه‌شناسی الهامی
│   │   ├── poem.html                             # نمایش یک شعر
│   │   ├── research_collaboration.html           # همکاری پژوهشی
│   │   ├── textual_criticism.html               # نقد و تصحیح متون
│   │   ├── word_398.html                         # قالب صفحه واژه ۳۹۸
│   │   ├── admin/                                # قالب‌های پنل مدیریت
│   │   │   ├── _sidebar.html                     # نوار کناری پنل
│   │   │   ├── change_role.html                  # تغییر نقش کاربران
│   │   │   ├── comments.html                     # مدیریت نظرات
│   │   │   ├── corrections.html                  # بررسی اصلاحات ابیات
│   │   │   ├── dashboard.html                    # داشبورد مدیریت
│   │   │   ├── recordings.html                   # مدیریت فایل‌های صوتی
│   │   │   └── users.html                        # مدیریت کاربران
│   │   ├── auth/                                 # قالب‌های احراز هویت
│   │   │   ├── change_password.html              # تغییر رمز عبور
│   │   │   ├── forgot_password.html              # درخواست بازیابی رمز
│   │   │   ├── login.html                        # صفحه ورود
│   │   │   ├── profile.html                      # پروفایل کاربر
│   │   │   ├── register.html                     # صفحه ثبت‌نام
│   │   │   └── reset_password.html               # تعیین رمز جدید
│   │   ├── emails/reset_password.html             # قالب ایمیل بازیابی رمز
│   │   ├── errors/500.html                        # صفحه خطای داخلی سرور
│   │   ├── research/                             # قالب‌های بخش پژوهش
│   │   │   ├── README.md                         # توضیحات قالب‌های پژوهش
│   │   │   ├── admin_form.html                   # فرم مدیریت پژوهش
│   │   │   ├── base_form.html                    # قالب پایه فرم‌های پژوهش
│   │   │   ├── manage_images.html                # مدیریت تصاویر پژوهشی
│   │   │   ├── researcher_form.html              # فرم ویژه محقق
│   │   │   ├── test_forms.html                   # قالب‌های آزمایشی فرم‌ها
│   │   │   └── view_only_form.html               # فرم فقط برای مشاهده
│   │   └── verses/                               # قالب‌های مربوط به اشعار
│   │       ├── compare_versions.html             # مقایسه نسخه‌های شعر
│   │       ├── my_recordings.html                # فایل‌های صوتی کاربر
│   │       └── record_audio.html                 # ضبط فایل صوتی شعر
│   └── static/                                  # فایل‌های ثابت سمت کاربر
│       ├── css/                                 # شیوه‌نامه‌های صفحات
│       │   ├── bootstrap.rtl.min.css            # Bootstrap راست‌چین فشرده
│       │   ├── style.css                        # شیوه‌نامه اصلی سایت
│       │   └── verse-corrections.css            # شیوه‌نامه اصلاحات ابیات
│       ├── js/                                  # اسکریپت‌های سمت کاربر
│       │   ├── bootstrap.bundle.min.js          # کتابخانه Bootstrap
│       │   ├── harakat.js                       # مدیریت و نمایش اعراب
│       │   ├── main.js                          # رفتارهای عمومی رابط کاربری
│       │   └── verse-corrections.js             # تعاملات اصلاحات ابیات
│       ├── images/                              # تصاویر و الگوهای سایت
│       │   ├── besm.png                         # تصویر بسم‌الله
│       │   ├── favicon.ico                      # نماد سایت در مرورگر
│       │   ├── form.png                         # تصویر فرم
│       │   ├── hand-write-1.jpg                 # تصویر دست‌نوشته شماره ۱
│       │   ├── hand-write-2.jpg                 # تصویر دست‌نوشته شماره ۲
│       │   ├── hand-write-3.jpg                 # تصویر دست‌نوشته شماره ۳
│       │   ├── hand-write-4.jpg                 # تصویر دست‌نوشته شماره ۴
│       │   ├── hoo.jpg                          # تصویر محتوایی سایت
│       │   ├── pattern.png                      # الگوی پس‌زمینه
│       │   ├── pattern1.png                     # الگوی تصویری شماره ۱
│       │   ├── pattern2.png                     # الگوی تصویری شماره ۲
│       │   ├── pattern4.png                     # الگوی تصویری شماره ۴
│       │   ├── poet.png                         # تصویر شاعر
│       │   └── poet - Copy.png                  # نسخه کپی تصویر شاعر
│       ├── fonts/                               # فونت‌های فارسی و آیکون‌ها
│       │   ├── Vazir.woff                       # فونت وزیر معمولی
│       │   ├── Vazir.woff2                      # نسخه فشرده فونت وزیر
│       │   ├── Vazir-Bold.woff                  # فونت وزیر ضخیم
│       │   ├── Vazir-Bold.woff2                 # نسخه فشرده فونت وزیر ضخیم
│       │   ├── Sahel.woff                       # فونت ساحل معمولی
│       │   ├── Sahel-Bold.woff                  # فونت ساحل ضخیم
│       │   └── fontawesome/                     # فونت آیکون Font Awesome
│       │       ├── css/all.min.css              # شیوه‌نامه آیکون‌ها
│       │       └── webfonts/                    # فایل‌های فونت آیکون
│       │           ├── fa-brands-400.ttf        # آیکون برندها در قالب TTF
│       │           ├── fa-brands-400.woff2      # آیکون برندها در قالب WOFF2
│       │           ├── fa-regular-400.ttf       # آیکون‌های معمولی در قالب TTF
│       │           ├── fa-regular-400.woff2     # آیکون‌های معمولی در قالب WOFF2
│       │           ├── fa-solid-900.ttf         # آیکون‌های ضخیم در قالب TTF
│       │           ├── fa-solid-900.woff2       # آیکون‌های ضخیم در قالب WOFF2
│       │           ├── fa-v4compatibility.ttf   # سازگاری Font Awesome نسخه ۴
│       │           └── fa-v4compatibility.woff2 # سازگاری Font Awesome نسخه ۴
│       ├── robots.txt                           # قوانین خزش موتورهای جست‌وجو
│       └── sitemap.xml                          # نقشه صفحات سایت
├── doc/features/                                # مستندات قابلیت‌های پروژه
│   └── verse-corrections-system.md              # مستندات سامانه اصلاحات ابیات
├── migrations/                                  # مهاجرت‌ها و نسخه‌بندی پایگاه داده
│   ├── alembic.ini                              # تنظیمات Alembic
│   ├── env.py                                   # محیط اجرای مهاجرت‌ها
│   ├── script.py.mako                           # الگوی ایجاد فایل مهاجرت
│   └── versions/                                # نسخه‌های مهاجرت پایگاه داده
│       ├── ae847c4565e9_initial_migration_base_state.py # مهاجرت اولیه
│       ├── 20240610_add_research_images_table.py # افزودن جدول تصاویر پژوهشی
│       ├── 20251002_add_visit_table.py          # افزودن جدول بازدیدها
│       └── 20260210_add_verse_corrections.py    # افزودن جدول اصلاحات ابیات
├── tests/                                       # آزمون‌های خودکار پروژه
│   ├── __init__.py                              # مقداردهی اولیه بسته آزمون‌ها
│   ├── test_basic.py                            # آزمون قابلیت‌های پایه
│   └── test_security.py                         # آزمون‌های امنیتی
├── instance/                                    # داده‌های محلی زمان اجرا
├── uploads/                                     # فایل‌های بارگذاری‌شده کاربران
│   ├── images/                                  # تصاویر عمومی بارگذاری‌شده
│   └── research_images/                         # تصاویر پژوهشی بارگذاری‌شده
├── .env.example                                 # نمونه متغیرهای محیطی
├── .gitignore                                   # فایل‌های نادیده‌گرفته‌شده Git
├── .htaccess                                    # تنظیمات وب‌سرور Apache
├── admin_create_admin.py                        # ایجاد کاربر مدیر
├── admin_excel_to_sqlite_temp.py                # انتقال موقت Excel به SQLite
├── admin_fix_title_ids_safe.py                  # اصلاح امن شناسه عنوان‌ها
├── admin_migrate_research_data.py               # انتقال داده‌های پژوهشی
├── config.py                                    # تنظیمات برنامه و محیط اجرا
├── docker-compose.yml                           # تعریف سرویس‌های Docker Compose
├── Dockerfile                                   # دستور ساخت تصویر Docker
├── nginx.conf                                   # تنظیمات وب‌سرور Nginx
├── populate_data.py                             # ورود داده‌های اولیه
├── requirements.txt                             # وابستگی‌های Python
├── run.py                                       # اجرای برنامه در محیط توسعه
├── wsgi.py                                      # نقطه ورود WSGI در تولید
└── yoyo.ini                                     # تنظیمات ابزار مهاجرت Yoyo
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
