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
    
    // اضافه کردن event listener برای انتخاب فیلد
    const fieldSelect = document.getElementById(`field-select-${verseId}`);
    if (fieldSelect) {
        fieldSelect.addEventListener('change', function() {
            updateOldTextPreview(verseId, this.value);
        });
    }
}

/**
 * ایجاد HTML فرم نظر تصحیحی
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
                <label for="field-select-${verseId}">
                    <i class="fas fa-list"></i> قسمت مورد نظر:
                </label>
                <select id="field-select-${verseId}" name="field_name" required ${isEdit ? 'disabled' : ''}>
                    <option value="">انتخاب کنید...</option>
                    <option value="verse_1" ${isEdit && correctionData.field_name === 'verse_1' ? 'selected' : ''}>مصراع اول</option>
                    <option value="verse_2" ${isEdit && correctionData.field_name === 'verse_2' ? 'selected' : ''}>مصراع دوم</option>
                    <option value="verse_1_tag" ${isEdit && correctionData.field_name === 'verse_1_tag' ? 'selected' : ''}>اعراب مصراع اول</option>
                    <option value="verse_2_tag" ${isEdit && correctionData.field_name === 'verse_2_tag' ? 'selected' : ''}>اعراب مصراع دوم</option>
                    <option value="variant_diff" ${isEdit && correctionData.field_name === 'variant_diff' ? 'selected' : ''}>اختلاف نسخ</option>
                    <option value="present_in_versions" ${isEdit && correctionData.field_name === 'present_in_versions' ? 'selected' : ''}>موجود در نسخه‌ها</option>
                </select>
            </div>
            
            <div class="form-group" id="old-text-preview-${verseId}" style="display: none;">
                <label>متن فعلی:</label>
                <div class="preview-box"></div>
            </div>
            
            <div class="form-group">
                <label for="correction-type-${verseId}">
                    <i class="fas fa-tag"></i> نوع تصحیح:
                </label>
                <select id="correction-type-${verseId}" name="correction_type" required>
                    <option value="text" ${isEdit && correctionData.correction_type === 'text' ? 'selected' : ''}>متن</option>
                    <option value="variant" ${isEdit && correctionData.correction_type === 'variant' ? 'selected' : ''}>نسخه</option>
                    <option value="vocalization" ${isEdit && correctionData.correction_type === 'vocalization' ? 'selected' : ''}>اعراب</option>
                    <option value="punctuation" ${isEdit && correctionData.correction_type === 'punctuation' ? 'selected' : ''}>نقطه‌گذاری</option>
                    <option value="other" ${isEdit && correctionData.correction_type === 'other' ? 'selected' : ''}>سایر</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="new-text-${verseId}">
                    <i class="fas fa-edit"></i> متن پیشنهادی: *
                </label>
                <textarea 
                    id="new-text-${verseId}" 
                    name="new_text" 
                    rows="3" 
                    required 
                    placeholder="متن پیشنهادی خود را وارد کنید..."
                >${isEdit ? correctionData.new_text : ''}</textarea>
            </div>
            
            <div class="form-group">
                <label for="note-${verseId}">
                    <i class="fas fa-comment"></i> توضیحات (اختیاری):
                </label>
                <textarea 
                    id="note-${verseId}" 
                    name="note" 
                    rows="3" 
                    placeholder="دلیل تصحیح، منابع، یا توضیحات بیشتر..."
                >${isEdit ? (correctionData.note || '') : ''}</textarea>
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
 * به‌روزرسانی پیش‌نمایش متن فعلی
 */
function updateOldTextPreview(verseId, fieldName) {
    const previewContainer = document.getElementById(`old-text-preview-${verseId}`);
    if (!previewContainer) return;
    
    if (!fieldName) {
        previewContainer.style.display = 'none';
        return;
    }
    
    // دریافت متن فعلی از DOM
    const verseElement = document.querySelector(`[data-verse-id="${verseId}"]`);
    if (!verseElement) return;
    
    let oldText = '';
    
    // بسته به فیلد انتخابی، متن مربوطه را پیدا کن
    if (fieldName === 'verse_1') {
        const verse1Element = verseElement.querySelector('.verse-1');
        oldText = verse1Element ? verse1Element.textContent.trim() : '';
    } else if (fieldName === 'verse_2') {
        const verse2Element = verseElement.querySelector('.verse-2');
        oldText = verse2Element ? verse2Element.textContent.trim() : '';
    } else if (fieldName.includes('tag')) {
        oldText = verseElement.dataset[fieldName] || '(خالی)';
    } else {
        oldText = verseElement.dataset[fieldName] || '(خالی)';
    }
    
    const previewBox = previewContainer.querySelector('.preview-box');
    if (previewBox) {
        previewBox.textContent = oldText || '(خالی)';
        previewContainer.style.display = 'block';
    }
}

/**
 * ارسال فرم نظر تصحیحی
 */
function submitCorrectionForm(event, verseId, correctionId = null) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        verse_id: verseId,
        field_name: formData.get('field_name'),
        correction_type: formData.get('correction_type'),
        new_text: formData.get('new_text').trim(),
        note: formData.get('note').trim()
    };
    
    // اعتبارسنجی
    if (!data.field_name || !data.new_text) {
        alert('لطفاً تمام فیلدهای الزامی را پر کنید');
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
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeCorrectionForm(verseId);
            loadVerseCorrections(verseId);
        } else {
            alert('خطا: ' + data.message);
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
    // دریافت اطلاعات نظر فعلی
    const correctionElement = document.querySelector(`[data-correction-id="${correctionId}"]`);
    if (!correctionElement) return;
    
    // استخراج داده‌ها از DOM (در حالت واقعی باید از API دریافت شود)
    // برای سادگی، فرض می‌کنیم داده‌ها در data attributes ذخیره شده‌اند
    
    alert('قابلیت ویرایش به زودی اضافه خواهد شد');
    // TODO: پیاده‌سازی کامل ویرایش
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
    const container = document.getElementById(`corrections-${verseId}`);
    const button = document.querySelector(`[data-verse-id="${verseId}"] .btn-toggle-corrections`);
    
    if (!container) return;
    
    if (container.style.display === 'none' || !container.style.display) {
        container.style.display = 'block';
        if (button) button.innerHTML = '<i class="fas fa-chevron-up"></i> بستن نظرات';
        
        // بارگذاری نظرات در صورت خالی بودن
        if (!container.hasAttribute('data-loaded')) {
            loadVerseCorrections(verseId);
            container.setAttribute('data-loaded', 'true');
        }
    } else {
        container.style.display = 'none';
        if (button) button.innerHTML = '<i class="fas fa-chevron-down"></i> نمایش نظرات تصحیحی';
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
