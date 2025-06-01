// اسکریپت اصلی سایت فردوسی حسینی

document.addEventListener('DOMContentLoaded', function() {
    
    // انیمیشن ورود ابیات
    animateVerses();
    
    // مدیریت نظرات
    handleComments();
    
    // مدیریت پخش صوت
    handleAudioPlayer();
    
    // مدیریت جستجو
    handleSearch();
    
    // مدیریت فرم‌ها
    handleForms();
    
    // مدیریت پنل ادمین
    handleAdminPanel();
});

// انیمیشن ورود ابیات
function animateVerses() {
    const verses = document.querySelectorAll('.verse');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add('show');
                }, index * 200);
            }
        });
    }, { threshold: 0.1 });

    verses.forEach(verse => {
        observer.observe(verse);
    });
}

// مدیریت نظرات
function handleComments() {
    const commentsToggle = document.getElementById('commentsToggle');
    const commentsContainer = document.getElementById('commentsContainer');
    
    if (commentsToggle && commentsContainer) {
        commentsToggle.addEventListener('click', function() {
            commentsContainer.classList.toggle('show');
            const isShowing = commentsContainer.classList.contains('show');
            this.textContent = isShowing ? 'مخفی کردن نظرات' : 'نمایش نظرات محققین';
        });
    }
}

// مدیریت پخش صوت
function handleAudioPlayer() {
    const audioSelect = document.getElementById('audioSelect');
    const playButton = document.getElementById('playButton');
    const audioPlayer = document.getElementById('audioPlayer');
    
    if (audioSelect && playButton && audioPlayer) {
        playButton.addEventListener('click', function() {
            const selectedFile = audioSelect.value;
            if (selectedFile) {
                audioPlayer.src = selectedFile;
                audioPlayer.play();
                this.textContent = 'در حال پخش...';
                this.disabled = true;
            } else {
                alert('لطفاً ابتدا یک خواننده انتخاب کنید.');
            }
        });
        
        audioPlayer.addEventListener('ended', function() {
            playButton.textContent = 'پخش';
            playButton.disabled = false;
        });
        
        audioPlayer.addEventListener('error', function() {
            playButton.textContent = 'پخش';
            playButton.disabled = false;
            alert('خطا در پخش فایل صوتی');
        });
    }
}

// مدیریت جستجو
function handleSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    
    if (searchForm && searchInput) {
        // ذخیره نتایج جستجوی قبلی
        let lastSearchResults = null;
        
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
        
        // جستجوی زنده
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.trim().length > 2) {
                    performSearch();
                }
            }, 500);
        });
        
        function performSearch() {
            const query = searchInput.value.trim();
            if (!query) return;
            
            showLoading(searchResults);
            
            fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                lastSearchResults = data.results;
                displaySearchResults(data.results);
            })
            .catch(error => {
                console.error('خطا در جستجو:', error);
                showError(searchResults, 'خطا در جستجو رخ داد');
            });
        }
        
        function displaySearchResults(results) {
            if (!searchResults) return;
            
            if (results.length === 0) {
                searchResults.innerHTML = '<div class="alert alert-info">نتیجه‌ای یافت نشد.</div>';
                return;
            }
            
            let html = '<div class="search-results-container"><h3>نتایج جستجو:</h3>';
            results.forEach(result => {
                const url = result.type === 'title' 
                    ? `/title/${result.id}` 
                    : `/title/${result.title_id}#verse-${result.id}`;
                    
                html += `
                    <div class="search-result-item" onclick="window.location.href='${url}'">
                        <div class="result-title">${result.title}</div>
                        <div class="result-match">${result.match}</div>
                        <div class="result-garden">${getGardenName(result.garden)}</div>
                    </div>
                `;
            });
            html += '</div>';
            
            searchResults.innerHTML = html;
        }
    }
}

// مدیریت فرم‌ها
function handleForms() {
    // فرم نظر
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            const textarea = this.querySelector('textarea');
            if (textarea && textarea.value.trim().length < 10) {
                e.preventDefault();
                alert('نظر باید حداقل ۱۰ کاراکتر باشد.');
                return;
            }
        });
    }
    
    // فرم آپلود صوت
    const audioForm = document.getElementById('audioForm');
    const audioFile = document.getElementById('audioFile');
    
    if (audioForm && audioFile) {
        audioFile.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // بررسی نوع فایل
                const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/m4a'];
                if (!allowedTypes.includes(file.type)) {
                    alert('فقط فایل‌های صوتی مجاز هستند.');
                    this.value = '';
                    return;
                }
                
                // بررسی حجم فایل (5 مگابایت)
                if (file.size > 5 * 1024 * 1024) {
                    alert('حجم فایل نباید بیشتر از ۵ مگابایت باشد.');
                    this.value = '';
                    return;
                }
            }
        });
        
        audioForm.addEventListener('submit', function(e) {
            const file = audioFile.files[0];
            if (!file) {
                e.preventDefault();
                alert('لطفاً یک فایل صوتی انتخاب کنید.');
                return;
            }
            
            // نمایش لودینگ
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'در حال آپلود...';
            }
        });
    }
}

// مدیریت پنل ادمین
function handleAdminPanel() {
    // دکمه‌های حذف
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('آیا مطمئن هستید؟')) {
                window.location.href = this.href;
            }
        });
    });
    
    // دکمه‌های بازنشانی رمز
    const resetButtons = document.querySelectorAll('.btn-reset');
    resetButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('آیا می‌خواهید رمز عبور این کاربر را بازنشانی کنید؟')) {
                window.location.href = this.href;
            }
        });
    });
}

// توابع کمکی
function showLoading(element) {
    if (element) {
        element.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p>در حال جستجو...</p>
            </div>
        `;
    }
}

function showError(element, message) {
    if (element) {
        element.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }
}

function getGardenName(gardenNumber) {
    const names = {
        1: 'خیابان اول باغ فردوس',
        2: 'خیابان دوم باغ فردوس',
        3: 'خیابان سوم باغ فردوس',
        4: 'خیابان چهارم باغ فردوس'
    };
    return names[gardenNumber] || `باغ ${gardenNumber}`;
}

// مدیریت تغییر اندازه تصویر
function handleImageResize() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('load', function() {
            if (this.naturalWidth > 800) {
                this.style.maxWidth = '100%';
                this.style.height = 'auto';
            }
        });
    });
}

// مدیریت اسکرول نرم
function smoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// مدیریت کپی متن
function handleTextCopy() {
    const verses = document.querySelectorAll('.verse');
    verses.forEach(verse => {
        verse.addEventListener('dblclick', function() {
            const text = this.textContent.trim();
            navigator.clipboard.writeText(text).then(() => {
                // نمایش پیام موفقیت
                const toast = document.createElement('div');
                toast.className = 'alert alert-success';
                toast.style.position = 'fixed';
                toast.style.top = '20px';
                toast.style.right = '20px';
                toast.style.zIndex = '9999';
                toast.textContent = 'متن کپی شد';
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 2000);
            }).catch(err => {
                console.error('خطا در کپی متن:', err);
            });
        });
    });
}

// راه‌اندازی تمام عملکردها
document.addEventListener('DOMContentLoaded', function() {
    handleImageResize();
    smoothScroll();
    handleTextCopy();
});

// مدیریت خطاهای شبکه
window.addEventListener('online', function() {
    const offlineAlert = document.getElementById('offlineAlert');
    if (offlineAlert) {
        offlineAlert.style.display = 'none';
    }
});

window.addEventListener('offline', function() {
    let offlineAlert = document.getElementById('offlineAlert');
    if (!offlineAlert) {
        offlineAlert = document.createElement('div');
        offlineAlert.id = 'offlineAlert';
        offlineAlert.className = 'alert alert-warning';
        offlineAlert.style.position = 'fixed';
        offlineAlert.style.top = '0';
        offlineAlert.style.left = '0';
        offlineAlert.style.right = '0';
        offlineAlert.style.zIndex = '9999';
        offlineAlert.style.textAlign = 'center';
        offlineAlert.textContent = 'اتصال اینترنت قطع شده است';
        document.body.appendChild(offlineAlert);
    }
    offlineAlert.style.display = 'block';
});

// مدیریت تم تاریک (اختیاری)
function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark-theme');
    
    if (isDark) {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
}

// بارگذاری تم ذخیره شده
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
});

// مدیریت اعلان‌ها
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// صادرات توابع برای استفاده در صفحات دیگر
window.FerdowsiApp = {
    showNotification,
    toggleTheme,
    showLoading,
    showError,
    getGardenName
};