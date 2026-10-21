فایل‌های TinyMCE (نسخه‌ی self-hosted، Community) را اینجا قرار دهید:

    app/articles/static/vendor/tinymce/tinymce.min.js
    app/articles/static/vendor/tinymce/langs/fa.js         (اختیاری، برای رابط فارسی)
    app/articles/static/vendor/tinymce/plugins/...
    app/articles/static/vendor/tinymce/skins/...

منبع دانلود: https://www.tiny.cloud/get-tiny/self-hosted/
یا: npm install tinymce   و سپس کپی از node_modules/tinymce به همین پوشه.

نیازی به API Key نیست چون از cdn.tiny.cloud استفاده نمی‌کنیم؛ همه‌چیز از
static خود سایت (app/articles/static) سرو می‌شود که با CSP فعلی سایت
(script-src 'self') هم سازگار است.
