import unicodedata


# ============================================================
# ۱. نگاشت حروف فارسی به حروف عربی
# ============================================================

PERSIAN_TO_ARABIC = {
    'گ': 'ک',
    'چ': 'ج',
    'پ': 'ب',
    'ژ': 'ز',
}


# ============================================================
# ۲. اسامی ۲۸ حرف الفبای عربی
#
# اولین حرف اسم = زبر
# بقیه حروف اسم = بینات
# ============================================================

LETTER_NAMES = {
    'ا': 'الف',
    'ب': 'با',
    'ت': 'تا',
    'ث': 'ثا',
    'ج': 'جیم',
    'ح': 'حا',
    'خ': 'خا',
    'د': 'دال',
    'ذ': 'ذال',
    'ر': 'را',
    'ز': 'زا',
    'س': 'سین',
    'ش': 'شین',
    'ص': 'صاد',
    'ض': 'ضاد',
    'ط': 'طا',
    'ظ': 'ظا',
    'ع': 'عین',
    'غ': 'غین',
    'ف': 'فا',
    'ق': 'قاف',
    'ک': 'کاف',
    'ل': 'لام',
    'م': 'میم',
    'ن': 'نون',
    'ه': 'ها',
    'و': 'واو',
    'ی': 'یا',
}

ARABIC_LETTERS = set(LETTER_NAMES.keys())


# ============================================================
# ۳. حذف حرکات و علائم اعراب
#
# فتحه، کسره، ضمه، سکون، تنوین، تشدید و...
# ============================================================

def remove_diacritics(text):
    """
    تمام علائم ترکیبی Unicode را حذف می‌کند.
    بنابراین حرکاتی مثل:
    َ ِ ُ ّ ْ ً ٍ ٌ
    و سایر علائم اعراب نادیده گرفته می‌شوند.
    """

    result = []

    for char in text:
        if unicodedata.category(char) != 'Mn':
            result.append(char)

    return ''.join(result)


# ============================================================
# ۴. نرمال‌سازی حروف
# ============================================================

def normalize_text(text):
    """
    - حذف حرکات
    - تبدیل حروف فارسی خاص به حروف عربی
    - نگه داشتن فقط ۲۸ حرف عربی
    """

    text = remove_diacritics(text)

    result = []

    for char in text:

        # تبدیل گ، چ، پ، ژ
        char = PERSIAN_TO_ARABIC.get(char, char)

        # فقط حروف ۲۸گانه
        if char in ARABIC_LETTERS:
            result.append(char)

    return ''.join(result)


# ============================================================
# ۵. حذف حروف تکراری با حفظ ترتیب
# ============================================================

def remove_duplicates(text):
    """
    حروف تکراری را از ابتدا به انتها حذف می‌کند
    و فقط اولین وقوع هر حرف را نگه می‌دارد.
    """

    seen = set()
    result = []

    for char in text:

        if char not in seen:
            seen.add(char)
            result.append(char)

    return ''.join(result)


# ============================================================
# ۶. به دست آوردن بینات یک حرف
# ============================================================

def get_bayenat(letter):
    """
    اسم حرف را پیدا می‌کند.

    مثال:
        ا -> الف -> لف
        س -> سين -> ين
        ب -> باء -> اء

    اولین حرف اسم = زبر
    بقیه = بینات
    """

    name = LETTER_NAMES[letter]

    # حذف تکرارهای بینات، با حفظ ترتیب
    bayenat = remove_duplicates(name[1:])

    return bayenat

# ============================================================
# ۶. تکثیر
# ============================================================
def taksir(text):
    """
    انجام عملیات تکسیر روی یک رشته.

    سطر اول = رشته اولیه

    هر سطر بعدی با این الگو ساخته می‌شود:
        آخرین حرف
        اولین حرف
        ماقبل آخر
        دومین حرف
        ...

    عملیات تا زمانی ادامه پیدا می‌کند که
    سطر جدید برابر سطر اول شود.

    خروجی:
        تمام سطرهای تکسیر
    """

    rows = [text]

    current = text

    while True:

        next_row = []

        left = 0
        right = len(current) - 1

        # ابتدا از انتها و سپس از ابتدا
        while left <= right:

            next_row.append(current[right])

            if left != right:
                next_row.append(current[left])

            left += 1
            right -= 1

        next_row = ''.join(next_row)

        # اگر به رشته اولیه رسیدیم، زمام ساخته شده است
        rows.append(next_row)

        if next_row == text:
            break

        current = next_row

    return rows



# ============================================================
# ۷. پردازش کامل
# ============================================================
def process_word_398(text):

    # مرحله اول: نرمال‌سازی
    normalized = normalize_text(text)

    # مرحله دوم: حذف حروف تکراری
    unique_letters = remove_duplicates(normalized)

    # مرحله سوم: استخراج بینات
    bayenat = {}

    for letter in unique_letters:
        bayenat[letter] = get_bayenat(letter)

    # مرحله چهارم:
    # حذف مکررات بین تمام بینات از ابتدا به انتها
    seen = set()
    bayenat_segmented_parts = []

    for letter in unique_letters:

        for char in bayenat[letter]:

            if char not in seen:
                seen.add(char)
                bayenat_segmented_parts.append(char)

    bayenat_segmented = ' '.join(bayenat_segmented_parts)

    # مرحله پنجم: تکسیر
    taksir_rows = taksir(
        bayenat_segmented.replace(' ', '')
    )

    return {
        'normalized': normalized,
        'unique_letters': unique_letters,
        'bayenat': bayenat,
        'bayenat_segmented': bayenat_segmented,
        'taksir': taksir_rows,
    }