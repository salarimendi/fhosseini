// app/articles/static/js/article-editor.js
// راه‌اندازی TinyMCE روی textarea با id="content_html" و اتصال دکمه‌ی
// تصویر آن به endpoint آپلود ماژول مقالات (که JSON با فیلد "location" برمی‌گرداند).

document.addEventListener('DOMContentLoaded', function () {
    var loaderScript = document.getElementById('tinymce-loader');
    var uploadUrl = loaderScript.getAttribute('data-upload-url');

    var csrfInput = document.querySelector('#article-form input[name="csrf_token"]');
    var csrfToken = csrfInput ? csrfInput.value : '';

    tinymce.init({
        selector: '#content_html',
        // نسخه‌ی self-hosted -> license_key: 'gpl' نیاز به api-key و
        // بارگذاری از cdn.tiny.cloud ندارد و با CSP سایت هم تداخل نمی‌کند.
        license_key: 'gpl',
        directionality: 'rtl',
        language: 'fa', // فایل زبان فارسی را از پکیج TinyMCE به vendor/tinymce/langs/ کپی کنید
        height: 500,
        menubar: 'edit view insert format table',
        plugins: 'link image lists table code searchreplace autolink wordcount',
        toolbar:
            'undo redo | blocks | bold italic underline strikethrough | ' +
            'alignleft aligncenter alignright | bullist numlist | ' +
            'link image table blockquote | code | removeformat',

        images_upload_url: uploadUrl,
        automatic_uploads: true,
        images_upload_handler: function (blobInfo) {
            return new Promise(function (resolve, reject) {
                var formData = new FormData();
                formData.append('file', blobInfo.blob(), blobInfo.filename());

                fetch(uploadUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData,
                })
                    .then(function (res) { return res.json(); })
                    .then(function (data) {
                        if (data.location) {
                            resolve(data.location);
                        } else {
                            reject(data.error || 'خطا در آپلود تصویر');
                        }
                    })
                    .catch(function (err) {
                        reject('خطا در ارتباط با سرور: ' + err);
                    });
            });
        },
    });
});


var articleForm = document.getElementById('article-form');

articleForm.addEventListener('submit', function () {
    tinymce.triggerSave();
});