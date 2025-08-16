#!/usr/bin/env python3
"""
Script to populate sample data for Ferdowsi Hosseini website
Usage: python populate_data.py
"""

from app import create_app, db
from app.models import Title, Verse, User

def populate_sample_data():
    """Populate database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Populating sample data for Ferdowsi Hosseini website")
        print("-" * 60)
        
        # Check if data already exists
        existing_titles = Title.query.count()
        if existing_titles > 0:
            response = input(f"Database already contains {existing_titles} titles. Continue? (y/N): ")
            if response.lower() != 'y':
                return
        
        try:
            # Sample data for four gardens (chapters)
            sample_data = {
                1: {  # باغ اول
                    'خیابان اول - آغاز سفر': [
                        ('در راه عشق که آغاز کردم', 'دل از هر غم آزاد کردم'),
                        ('به باغ فردوس قدم نهادم', 'گل و گلستان بنیاد کردم'),
                        ('چو بلبل عاشق آوازه سرایم', 'که عشق و محبت را پیش برایم')
                    ],
                    'نغمه عاشقان': [
                        ('عاشقان در این سراینده', 'دل به عشق حق سپارنده'),
                        ('نغمه‌ای از عالم قدس', 'در دل و جان ما نگارنده'),
                        ('ای خدا ما را به منزل', 'رسان و راه نمایان کن')
                    ]
                },
                2: {  # باغ دوم
                    'خیابان دوم - راه عشق': [
                        ('در این خیابان دوم باغ فردوس', 'رموز عشق و محبت است محسوس'),
                        ('هر قدم در این مسیر پر برکت', 'نشانی از رحمت یزدان است'),
                        ('عاشقان این راه را می‌پیمایند', 'به سوی حضرت احدیت می‌تازند')
                    ],
                    'منزل عارفان': [
                        ('عارفان در این منزل آرام یافته', 'دل از دنیا و مافیها رها کرده'),
                        ('در خلوت با دوست سر گفته', 'راز عشق را در دل نهفته'),
                        ('چشم دل بر حق گشاده شده', 'نور ایمان در وجود تابیده')
                    ]
                },
                3: {  # باغ سوم
                    'خیابان سوم - معرفت': [
                        ('سومین خیابان باغ فردوس', 'منزل اهل معرفت است محسوس'),
                        ('در این مقام دل پاک می‌شود', 'روح از کدورت‌ها باک می‌شود'),
                        ('نور حقیقت بر دل می‌تابد', 'راه سالک را روشن می‌نماید')
                    ],
                    'مقام صبر و شکر': [
                        ('صبر و شکر دو بال پرواز است', 'که سالک را به عرش می‌برد راست'),
                        ('صبر در محنت و شکر در نعمت', 'راه کمال و سعادت حقیقت'),
                        ('هر که این دو را بر خود عادت کرد', 'به مقصود اصلی اراده کرد')
                    ]
                },
                4: {  # باغ چهارم
                    'خیابان چهارم - وصال': [
                        ('چهارمین خیابان منزل وصال', 'جایگاه تجلی جمال و جلال'),
                        ('در اینجا عاشق و معشوق یکی', 'نه دوئی نه کثرت بلکه وحدت‌نکی'),
                        ('فنا فی‌الله باقی بالله است', 'که منتهای سلوک عاشق راست')
                    ],
                    'ختم کلام': [
                        ('پایان کلام چهار خیابان', 'باغ فردوس اهل ایمان'),
                        ('الهامی کرمانشاهی این نغمه سرود', 'تا دل عاشقان شاد و خرم شود'),
                        ('دعا کن که ما نیز این راه بپیماییم', 'و در باغ فردوس جای بیاراییم')
                    ]
                }
            }
            
            # Populate database
            title_count = 0
            verse_count = 0
            
            for garden_num, titles_data in sample_data.items():
                print(f"Adding garden {garden_num} (باغ {garden_num})...")
                
                title_order = 1
                for title_text, verses_data in titles_data.items():
                    # Create title
                    title = Title(
                        title=title_text,
                        garden=garden_num,
                        order_in_garden=title_order
                    )
                    db.session.add(title)
                    db.session.flush()  # Get the ID
                    title_count += 1
                    
                    # Create verses for this title
                    verse_order = 1
                    for verse_1, verse_2 in verses_data:
                        verse = Verse(
                            title_id=title.id,
                            order_in_title=verse_order,
                            verse_1=verse_1,
                            verse_2=verse_2
                        )
                        db.session.add(verse)
                        verse_count += 1
                        verse_order += 1
                    
                    title_order += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"\n✅ Sample data populated successfully!")
            print(f"📚 Created {title_count} titles")  
            print(f"📝 Created {verse_count} verses")
            print(f"🌸 Created 4 gardens (باغ)")
            
            print(f"\nSample structure:")
            for garden_num in sample_data.keys():
                titles = Title.query.filter_by(garden=garden_num).all()
                print(f"  باغ {garden_num}: {len(titles)} titles")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error populating data: {str(e)}")
            raise

def create_sample_users():
    """Create sample users for testing"""
    app = create_app()
    
    with app.app_context():
        print("\nCreating sample users...")
        
        try:
            # Sample researcher
            researcher = User(
                username='محقق_نمونه',
                email='researcher@example.com',
                role='researcher',
                is_active=True
            )
            researcher.set_password('password123')
            db.session.add(researcher)
            
            # Sample reader
            reader = User(
                username='خواننده_نمونه',
                email='reader@example.com', 
                role='reader',
                is_active=True
            )
            reader.set_password('password123')
            db.session.add(reader)
            
            db.session.commit()
            print("✅ Sample users created:")
            print("   - محقق_نمونه (researcher@example.com) - password: password123")
            print("   - خواننده_نمونه (reader@example.com) - password: password123")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample users: {str(e)}")

if __name__ == '__main__':
    populate_sample_data()
    
    response = input("\nCreate sample users for testing? (y/N): ")
    if response.lower() == 'y':
        create_sample_users()
    
    print("\n🎉 Setup complete! You can now run the application with: python run.py")