# ساختار جدید فرم‌های پژوهشی

## بررسی کلی

فرم‌های پژوهشی به پنج فایل جداگانه تقسیم شده‌اند تا مدیریت و نگهداری آسان‌تر شود:

### فایل‌های موجود:

1. **`base_form.html`** - فرم پایه مشترک
   - شامل تمام فیلدهای مشترک
   - منطق پایه برای نمایش فرم
   - قابل گسترش توسط سایر فرم‌ها
   - شامل استایل‌های مشترک

2. **`researcher_form.html`** - فرم ویرایش نظر (محقق)
   - برای محققین در صفحه شعر
   - امکان ویرایش نظر موجود
   - مدیریت کامل عکس‌ها و زیرموضوعات
   - endpoint: `/verses/submit_research_form/`

3. **`view_only_form.html`** - فرم مشاهده
   - حالت فقط خواندنی
   - نمایش عکس‌ها بدون امکان ویرایش
   - برای مشاهده عمومی در انتهای شعر
   - auto-resize برای textarea ها

4. **`admin_form.html`** - فرم ادمین
   - برای ادمین در پنل مدیریت
   - امکان ویرایش نظر (بدون اضافه کردن)
   - مدیریت کامل عکس‌ها و زیرموضوعات
   - endpoint: `/admin/comments/{id}/research-update`

## مزایای ساختار جدید:

### ۱. استقلال کامل
- هر فرم در فایل جداگانه
- تغییرات آینده تداخل ندارند
- تست آسان‌تر

### ۲. نگهداری آسان
- کد تمیز و منظم
- منطق هر حالت مشخص است
- رفع اشکال آسان‌تر

### ۳. قابلیت توسعه
- اضافه کردن حالت‌های جدید آسان
- تغییرات در یک فرم روی سایرین تأثیر نمی‌گذارد

### ۴. عملکرد بهتر
- بارگذاری فقط کد مورد نیاز
- بهینه‌سازی برای هر حالت

## نحوه استفاده:

### برای محقق (اضافه کردن نظر جدید):
### برای محقق (ویرایش نظر موجود):
```python
return render_template('research/researcher_form.html', 
    title_id=title_id, 
    poem_title=poem_title, 
    comment_data=comment_data, 
    comment=comment)
```

### برای مشاهده عمومی:
```python
return render_template('research/view_only_form.html', 
    poem_title=poem_title, 
    comment_data=comment_data, 
    comment=comment, 
    username=comment.author_name,
    return_url=return_url)
```

### برای ادمین:
```python
return render_template('research/admin_form.html', 
    poem_title=poem_title, 
    comment_data=comment_data, 
    comment=comment)
```

## نکات مهم:

1. **فایل پایه**: تمام منطق مشترک در `base_form.html` قرار دارد
2. **بلوک‌های Jinja2**: هر فرم می‌تواند بخش‌های خاص خود را override کند
3. **JavaScript**: هر فرم JavaScript مخصوص خود را دارد
4. **Route ها**: هر route فایل مناسب را render می‌کند

## تغییرات آینده:

برای اضافه کردن قابلیت جدید:
1. ابتدا در `base_form.html` اضافه کنید (اگر مشترک است)
2. سپس در فرم‌های خاص override کنید (اگر متفاوت است)
3. JavaScript مربوطه را در فایل مناسب اضافه کنید

این ساختار تضمین می‌کند که تغییرات آینده به راحتی مدیریت شوند و تداخلی ایجاد نشود. 