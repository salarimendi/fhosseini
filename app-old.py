from flask import Flask, render_template, request
import sqlite3
import os
import re
import webbrowser

app = Flask(__name__)

# مسیر فایل دیتابیس صحیح
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'poetry.db')  # نام فایل اصلاح شد

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    gardens = {1: {}, 2: {}, 3: {}, 4: {}}

    cursor.execute("SELECT id, title, garden FROM titles")
    titles = cursor.fetchall()

    for t in titles:
        garden_num = t['garden']
        title_id = t['id']
        title_name = t['title']
        gardens[garden_num][title_id] = {'title': title_name, 'verses': []}

    cursor.execute("SELECT title_id, verse_1, verse_2 FROM verses")
    verses = cursor.fetchall()

    for v in verses:
        title_id = v['title_id']
        verse_1 = v['verse_1']
        verse_2 = v['verse_2']

        for garden_num in gardens:
            if title_id in gardens[garden_num]:
                gardens[garden_num][title_id]['verses'].append((verse_1, verse_2))
                break

    conn.close()
    return gardens

gardens = load_data()

@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()
    results = []

    if search_query:
        pattern = re.compile(re.escape(search_query))

        for garden_num, garden in gardens.items():
            for title_id, title_data in garden.items():
                match_in_title = isinstance(title_data['title'], str) and re.search(pattern, title_data['title'])

                match_in_verses = any(
                    (isinstance(v1, str) and re.search(pattern, v1)) or
                    (isinstance(v2, str) and re.search(pattern, v2))
                    for v1, v2 in title_data['verses']
                )

                if match_in_title or match_in_verses:
                    results.append({
                        'garden_num': garden_num,
                        'title_id': title_id,
                        'title': title_data['title']
                    })

    return render_template('home.html', results=results, search_query=search_query, gardens=gardens)

@app.route('/garden/<int:garden_num>')
def garden(garden_num):
    garden = gardens[garden_num]
    return render_template('garden.html', garden=garden, garden_num=garden_num)

@app.route('/garden/<int:garden_num>/title/<int:title_id>')
def title(garden_num, title_id):
    title_data = gardens[garden_num][title_id]
    return render_template('title.html', title_data=title_data, garden_num=garden_num)

# فیلتر اعداد فارسی
def to_persian_number(number):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_digits[int(d)] if d.isdigit() else d for d in str(number))

app.jinja_env.filters['persian'] = to_persian_number

# فیلتر ترتیب فارسی
def persian_ordinal(n):
    ordinals = {
        1: 'اول', 2: 'دوم', 3: 'سوم', 4: 'چهارم',
        5: 'پنجم', 6: 'ششم', 7: 'هفتم', 8: 'هشتم', 9: 'نهم', 10: 'دهم'
    }
    return ordinals.get(n, str(n))

app.jinja_env.filters['persian_ordinal'] = persian_ordinal

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
