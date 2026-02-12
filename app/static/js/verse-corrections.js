// ====================================
// نظرات تصحیحی ابیات
// Verse Corrections Functionality
// ====================================

/**
 * بارگذاری نظرات تصحیحی یک بیت
 */
function loadVerseCorrections(verseId) {
    const container = document.getElementById(`corrections-${verseId}`);
    if (!container) return;
    
    // نمایش لودینگ
    container.innerHTML = '<div class="corrections-loading"><i class="fas fa-spinner fa-spin"></i> در حال بارگذاری...</div>';
    
    fetch(`/api/verse/${verseId}/corrections`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayVerseCorrections(verseId, data.corrections);
            } else {
                container.innerHTML = '<div class="corrections-error">خطا در بارگذاری نظرات</div>';
            }
        })
        .catch(error => {
            console.error('Error loading corrections:', error);
            container.innerHTML = '<div class="corrections-error">خطا در ارتباط با سرور</div>';
        });
}

/**
 * نمایش نظرات تصحیحی
 */
function displayVerseCorrections(verseId, corrections) {
    const container = document.getElementById(`corrections-${verseId}`);
    if (!container) return;
    
    if (corrections.length === 0) {
        container.innerHTML = '<div class="no-corrections">هنوز نظر تصحیحی ثبت نشده است</div>';
        return;
    }
    
    let html = '<div class="corrections-list">';
    
    corrections.forEach(correction => {
        const isApproved = correction.is_approved;
        const isPending = !isApproved;
        const isOwner = window.currentUserId && correction.created_by === window.currentUserId;
        
        html += `
        <div class="correction-item ${isPending ? 'pending' : 'approved'}" data-correction-id="${correction.id}">
            <div class="correction-header">
                <div class="correction-user">
                    <i class="fas fa-user-circle"></i>
                    <strong>${correction.created_by_fullname}</strong>
                    ${isPending ? '<span class="pending-badge">در انتظار تایید</span>' : ''}
                </div>
                <div class="correction-date">
                    <i class="fas fa-calendar-alt"></i>
                    ${formatDate(correction.created_at)}
                </div>
            </div>
            
            <div class="correction-body">
                <div class="correction-field-info">
                    <span class="field-badge">${getFieldNamePersian(correction.field_name)}</span>
                    <span class="type-badge type-${correction.correction_type}">${getCorrectionTypePersian(correction.correction_type)}</span>
                </div>
                
                <div class="correction-texts">
                    <div class="text-item old-text">
                        <div class="text-label">متن فعلی:</div>
                        <div class="text-content">${correction.old_text || '(خالی)'}</div>
                    </div>
                    <div class="text-arrow">
                        <i class="fas fa-arrow-left"></i>
                    </div>
                    <div class="text-item new-text">
                        <div class="text-label">متن پیشنهادی:</div>
                        <div class="text-content">${correction.new_text}</div>
                    </div>
                </div>
                
                ${correction.note ? `
                <div class="correction-note">
                    <i class="fas fa-comment-dots"></i>
                    <strong>توضیحات:</strong> ${correction.note}
                </div>
                ` : ''}
            </div>
            
            ${isOwner && isPending ? `
            <div class="correction-actions">
                <button class="btn-edit-correction" onclick="editVerseCorrection(${correction.id}, ${verseId})">
                    <i class="fas fa-edit"></i> ویرایش
                </button>
                <button class="btn-delete-correction" onclick="deleteVerseCorrection(${correction.id}, ${verseId})">
                    <i class="fas fa-trash"></i> حذف
                </button>
            </div>
            ` : ''}
            
            ${isApproved && correction.approved_at ? `
            <div class="correction-approval">
                <i class="fas fa-check-circle"></i>
                تایید شده توسط مدیر در ${formatDate(correction.approved_at)}
            </div>
            ` : ''}
        </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * نمایش فرم افزودن نظر تصحیحی
 */
function showCorrectionForm(verseId) {
    // بررسی لاگین بودن
    if (!window.isAuthenticated) {
        alert('برای ثبت نظر تصحیحی باید وارد سیستم شوید');
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        return;
    }
    
    // بررسی نقش کاربر
    if (!window.canComment) {
        alert('شما مجوز ثبت نظر تصحیحی را ندارید. فقط محققان می‌توانند نظر تصحیحی ثبت کنند.');
        return;
    }
    
    const formContainer = document.getElementById(`correction-form-${verseId}`);
    if (!formContainer) return;
    
    // اگر فرم قبلاً نمایش داده شده، پنهانش کن
    if (formContainer.style.display === 'block') {
        formContainer.style.display = 'none';
        return;
    }
    
    // ایجاد فرم
    formContainer.innerHTML = createCorrectionForm(verseId);
    formContainer.style.display = 'block';
    
    // فوکوس روی textarea
    setTimeout(() => {
        const textarea = document.getElementById(`new-text-${verseId}`);
        if (textarea) textarea.focus();
    }, 100);
}

/**
 * ایجاد HTML فرم نظر تصحیحی - ساده‌شده
 */
function createCorrectionForm(verseId, correctionData = null) {
    const isEdit = correctionData !== null;
    
    return `
    <div class="correction-form-wrapper">
        <div class="form-header">
            <h4>${isEdit ? 'ویرایش نظر تصحیحی' : 'ثبت نظر تصحیحی جدید'}</h4>
            <button class="btn-close-form" onclick="closeCorrectionForm(${verseId})">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <form id="correction-form-${verseId}" onsubmit="submitCorrectionForm(event, ${verseId}, ${isEdit ? correctionData.id : 'null'})">
            <div class="form-group">
                <label for="new-text-${verseId}">
                    <i class="fas fa-comment-dots"></i> نظر تصحیحی شما: *
                </label>
                <textarea 
                    id="new-text-${verseId}" 
                    name="new_text" 
                    rows="4" 
                    required 
                    placeholder="نظر تصحیحی خود را وارد کنید (شامل توضیح تصحیح، منابع، یا پیشنهادات)"
                >${isEdit ? correctionData.new_text : ''}</textarea>
            </div>
            
            <div class="form-actions">
                <button type="submit" class="btn-submit-correction">
                    <i class="fas fa-check"></i> ${isEdit ? 'ذخیره تغییرات' : 'ثبت نظر'}
                </button>
                <button type="button" class="btn-cancel" onclick="closeCorrectionForm(${verseId})">
                    <i class="fas fa-times"></i> انصراف
                </button>
            </div>
        </form>
    </div>
    `;
}



/**
 * ارسال فرم نظر تصحیحی - ساده‌شده
 */
function submitCorrectionForm(event, verseId, correctionId = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        verse_id: verseId,
        new_text: formData.get('new_text').trim()
    };
    
    // اعتبارسنجی
    if (!data.new_text) {
        alert('لطفاً نظر خود را وارد کنید');
        return;
    }
    
    // نمایش لودینگ
    const submitBtn = form.querySelector('.btn-submit-correction');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> در حال ارسال...';
    
    const url = correctionId 
        ? `/api/verse/correction/${correctionId}/edit`
        : '/api/verse/correction/add';
    
    const method = correctionId ? 'PUT' : 'POST';
    
    // دریافت CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(responseData => {
        if (responseData.success) {
            alert(responseData.message);
            closeCorrectionForm(verseId);
            loadVerseCorrections(verseId);
        } else {
            alert('خطا: ' + responseData.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('خطا در ارتباط با سرور');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

/**
 * بستن فرم نظر تصحیحی
 */
function closeCorrectionForm(verseId) {
    const formContainer = document.getElementById(`correction-form-${verseId}`);
    if (formContainer) {
        formContainer.style.display = 'none';
        formContainer.innerHTML = '';
    }
}

/**
 * ویرایش نظر تصحیحی
 */
function editVerseCorrection(correctionId, verseId) {
    // دریافت اطلاعات نظر از سرور
    fetch(`/api/verse/${verseId}/corrections`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const correction = data.corrections.find(c => c.id === correctionId);
                if (!correction) {
                    alert('نظر مورد نظر یافت نشد');
                    return;
                }
                
                // بستن فرم افزودن اگر باز است
                closeCorrectionForm(verseId);
                
                // نمایش فرم ویرایش
                const formContainer = document.getElementById(`correction-form-${verseId}`);
                if (!formContainer) return;
                
                formContainer.innerHTML = createCorrectionForm(verseId, correction);
                formContainer.style.display = 'block';
                
                // فوکوس روی textarea
                setTimeout(() => {
                    const textarea = document.getElementById(`new-text-${verseId}`);
                    if (textarea) textarea.focus();
                }, 100);
            } else {
                alert('خطا در دریافت اطلاعات نظر');
            }
        })
        .catch(error => {
            console.error('Error loading correction:', error);
            alert('خطا در ارتباط با سرور');
        });
}

/**
 * حذف نظر تصحیحی
 */
function deleteVerseCorrection(correctionId, verseId) {
    if (!confirm('آیا از حذف این نظر تصحیحی اطمینان دارید؟')) {
        return;
    }
    
    // دریافت CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    fetch(`/api/verse/correction/${correctionId}/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            loadVerseCorrections(verseId);
        } else {
            alert('خطا: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('خطا در ارتباط با سرور');
    });
}

/**
 * Toggle نمایش نظرات تصحیحی
 */
function toggleCorrections(verseId) {
    const section = document.getElementById(`verse-section-${verseId}`);
    const button = document.querySelector(`[data-verse-id="${verseId}"]`);
    const container = document.getElementById(`corrections-${verseId}`);
    
    if (!section || !button) return;
    
    const isVisible = section.style.display !== 'none';
    
    if (isVisible) {
        // بسته کردن سکشن
        section.style.display = 'none';
        button.setAttribute('data-expanded', 'false');
        button.title = 'نمایش نظرات تصحیحی';
    } else {
        // باز کردن سکشن
        section.style.display = 'block';
        button.setAttribute('data-expanded', 'true');
        button.title = 'پنهان کردن نظرات تصحیحی';
        
        // بارگذاری نظرات در صورت خالی بودن
        if (container && !container.hasAttribute('data-loaded')) {
            loadVerseCorrections(verseId);
            container.setAttribute('data-loaded', 'true');
        }
    }
}

/**
 * توابع کمکی
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}/${month}/${day} - ${hours}:${minutes}`;
}

function getFieldNamePersian(fieldName) {
    const names = {
        'verse_1': 'مصراع اول',
        'verse_2': 'مصراع دوم',
        'verse_1_tag': 'اعراب مصراع اول',
        'verse_2_tag': 'اعراب مصراع دوم',
        'variant_diff': 'اختلاف نسخ',
        'present_in_versions': 'موجود در نسخه‌ها'
    };
    return names[fieldName] || fieldName;
}

function getCorrectionTypePersian(correctionType) {
    const types = {
        'text': 'متن',
        'variant': 'نسخه',
        'vocalization': 'اعراب',
        'punctuation': 'نقطه‌گذاری',
        'other': 'سایر'
    };
    return types[correctionType] || correctionType;
}

/**
 * تبدیل نمایش/مخفی کردن تمام نظرات تصحیحی
 */
function toggleAllCorrections() {
    const allSections = document.querySelectorAll('[id^="verse-section-"]');
    const allButtons = document.querySelectorAll('.btn-toggle-verse-corrections');
    const toggleBtn = document.getElementById('toggleAllCorrectionsBtn');
    
    if (allSections.length === 0) return;
    
    // بررسی وضعیت فعلی: اگر بیشتر سکشن‌ها پنهان باشند، همه را نمایش بده
    const visibleCount = Array.from(allSections).filter(section => {
        return section.style.display !== 'none';
    }).length;
    
    const shouldShow = visibleCount < allSections.length / 2;
    
    // تغییر وضعیت تمام سکشن‌ها
    allSections.forEach((section, index) => {
        const verseId = section.id.replace('verse-section-', '');
        const button = document.querySelector(`[data-verse-id="${verseId}"]`);
        const container = document.getElementById(`corrections-${verseId}`);
        
        if (shouldShow) {
            // نمایش سکشن
            section.style.display = 'block';
            if (button) {
                button.setAttribute('data-expanded', 'true');
                button.title = 'پنهان کردن نظرات تصحیحی';
            }
            
            // بارگذاری نظرات اگر هنوز بارگذاری نشده‌اند
            if (container && !container.hasAttribute('data-loaded')) {
                loadVerseCorrections(verseId);
                container.setAttribute('data-loaded', 'true');
            }
        } else {
            // مخفی کردن سکشن
            section.style.display = 'none';
            if (button) {
                button.setAttribute('data-expanded', 'false');
                button.title = 'نمایش نظرات تصحیحی';
            }
        }
    });
    
    // تغییر آیکون دکمه toggle همه
    if (toggleBtn) {
        const icon = toggleBtn.querySelector('i');
        if (icon) {
            icon.className = shouldShow ? 'fas fa-eye-slash ms-1' : 'fas fa-eye ms-1';
        }
    }
}

// ====================================
// Auto-load corrections on page load
// ====================================
document.addEventListener('DOMContentLoaded', function() {
    // اگر در صفحه شعر هستیم و hash مشخص شده، به آن بیت اسکرول کن
    if (window.location.hash && window.location.hash.startsWith('#verse-')) {
        const verseId = window.location.hash.replace('#verse-', '');
        setTimeout(() => {
            const element = document.querySelector(`[data-verse-id="${verseId}"]`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                element.classList.add('highlight-verse');
                
                // حذف هایلایت بعد از 3 ثانیه
                setTimeout(() => {
                    element.classList.remove('highlight-verse');
                }, 3000);
            }
        }, 500);
    }
});
