#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت مهاجرت داده‌های نظرات پژوهشی
تبدیل فیلدهای historical_flaw و reform_theory به ساختار جدید
"""

import json
from app import create_app, db
from app.models import Comment

def migrate_research_comments():
    """
    تبدیل تمام نظرات پژوهشی به ساختار جدید
    """
    app = create_app()
    
    with app.app_context():
        # پیدا کردن تمام نظرات پژوهشی
        all_comments = Comment.query.all()
        
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        print(f"شروع مهاجرت {len(all_comments)} نظر...")
        print("-" * 60)
        
        for comment in all_comments:
            try:
                # تلاش برای پارس کردن JSON
                try:
                    comment_data = json.loads(comment.comment)
                except (json.JSONDecodeError, TypeError):
                    # اگر JSON نیست، احتمالاً نظر متنی ساده است
                    skipped_count += 1
                    continue
                
                # بررسی اینکه آیا این یک فرم پژوهشی است
                if not isinstance(comment_data, dict):
                    skipped_count += 1
                    continue
                
                # اگر قبلاً مهاجرت شده (دارای primary_theory است)
                if 'primary_theory' in comment_data:
                    print(f"  ✓ نظر {comment.id} قبلاً مهاجرت شده")
                    skipped_count += 1
                    continue
                
                # اگر فیلدهای قدیمی وجود دارد
                has_old_fields = 'historical_flaw' in comment_data or 'reform_theory' in comment_data
                
                if has_old_fields:
                    # ادغام فیلدهای قدیمی
                    historical_flaw = comment_data.get('historical_flaw', '').strip()
                    reform_theory = comment_data.get('reform_theory', '').strip()
                    
                    # ایجاد نظریه محقق اصلی از ادغام دو فیلد
                    primary_theory_parts = []
                    
                    if historical_flaw:
                        primary_theory_parts.append("=== نقص تاریخی ===")
                        primary_theory_parts.append(historical_flaw)
                    
                    if reform_theory:
                        if primary_theory_parts:
                            primary_theory_parts.append("\n")
                        primary_theory_parts.append("=== نظریه اصلاحی ===")
                        primary_theory_parts.append(reform_theory)
                    
                    primary_theory = "\n".join(primary_theory_parts)
                    
                    # به‌روزرسانی ساختار
                    comment_data['primary_theory'] = primary_theory
                    comment_data['review_theory'] = ''
                    comment_data['final_theory'] = ''
                    
                    # حذف فیلدهای قدیمی
                    comment_data.pop('historical_flaw', None)
                    comment_data.pop('reform_theory', None)
                    
                    # ذخیره تغییرات
                    comment.comment = json.dumps(comment_data, ensure_ascii=False)
                    
                    print(f"  ✓ نظر {comment.id} مهاجرت یافت (نویسنده: {comment.author_name})")
                    updated_count += 1
                else:
                    # اگر فیلدهای قدیمی ندارد اما ساختار جدید هم ندارد
                    # فیلدهای خالی اضافه می‌کنیم
                    if 'form_type' in comment_data:  # احتمالاً یک فرم پژوهشی است
                        comment_data['primary_theory'] = ''
                        comment_data['review_theory'] = ''
                        comment_data['final_theory'] = ''
                        comment.comment = json.dumps(comment_data, ensure_ascii=False)
                        print(f"  ✓ نظر {comment.id} به ساختار جدید تبدیل شد")
                        updated_count += 1
                    else:
                        skipped_count += 1
                        
            except Exception as e:
                print(f"  ✗ خطا در مهاجرت نظر {comment.id}: {str(e)}")
                error_count += 1
                continue
        
        # ذخیره تغییرات
        try:
            db.session.commit()
            print("-" * 60)
            print("✓ مهاجرت با موفقیت انجام شد!")
            print(f"  - به‌روز شده: {updated_count}")
            print(f"  - رد شده: {skipped_count}")
            print(f"  - خطا: {error_count}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ خطا در ذخیره تغییرات: {str(e)}")
            return False
        
        return True

def rollback_migration():
    """
    بازگردانی مهاجرت (برای تست)
    تبدیل primary_theory به historical_flaw و reform_theory
    """
    app = create_app()
    
    with app.app_context():
        all_comments = Comment.query.all()
        
        rolled_back = 0
        
        print("شروع بازگردانی مهاجرت...")
        print("-" * 60)
        
        for comment in all_comments:
            try:
                comment_data = json.loads(comment.comment)
                
                if 'primary_theory' in comment_data:
                    primary = comment_data.get('primary_theory', '')
                    
                    # تلاش برای جدا کردن دو بخش
                    parts = primary.split('=== نظریه اصلاحی ===')
                    
                    if len(parts) == 2:
                        historical = parts[0].replace('=== نقص تاریخی ===', '').strip()
                        reform = parts[1].strip()
                    else:
                        historical = primary
                        reform = ''
                    
                    comment_data['historical_flaw'] = historical
                    comment_data['reform_theory'] = reform
                    
                    # حذف فیلدهای جدید
                    comment_data.pop('primary_theory', None)
                    comment_data.pop('review_theory', None)
                    comment_data.pop('final_theory', None)
                    
                    comment.comment = json.dumps(comment_data, ensure_ascii=False)
                    rolled_back += 1
                    print(f"  ✓ نظر {comment.id} بازگردانی شد")
                    
            except Exception as e:
                print(f"  ✗ خطا در بازگردانی نظر {comment.id}: {str(e)}")
        
        db.session.commit()
        print("-" * 60)
        print(f"✓ بازگردانی انجام شد. تعداد: {rolled_back}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback_migration()
    else:
        migrate_research_comments()