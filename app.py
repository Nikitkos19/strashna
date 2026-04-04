from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
from typing import List, Dict

app = Flask(__name__)

# Путь к файлу с объявлениями
ADS_FILE = 'ads.json'


# Функция для загрузки объявлений из JSON
def load_ads() -> List[Dict]:
    if not os.path.exists(ADS_FILE):
        # Если файла нет - создаем пустой список
        save_ads([])
        return []

    with open(ADS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# Функция для сохранения объявлений в JSON
def save_ads(ads: List[Dict]):
    with open(ADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    # Загружаем все объявления
    all_ads = load_ads()

    # Получаем параметры поиска и категории
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')

    # Фильтрация
    filtered_ads = all_ads.copy()

    if search_query:
        filtered_ads = [
            ad for ad in filtered_ads
            if search_query.lower() in ad['title'].lower()
               or search_query.lower() in ad['description'].lower()
        ]

    if category_filter and category_filter != 'Все':
        filtered_ads = [ad for ad in filtered_ads if ad['category'] == category_filter]

    # Сортируем от новых к старым (по id в обратном порядке)
    filtered_ads.sort(key=lambda x: x['id'], reverse=True)

    # Список уникальных категорий
    categories = ['Все'] + sorted(list(set([ad['category'] for ad in all_ads])))

    return render_template('index.html',
                           ads=filtered_ads,
                           search_query=search_query,
                           category_filter=category_filter,
                           categories=categories)


@app.route('/add', methods=['GET', 'POST'])
def add_ad():
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        category = request.form.get('category', '').strip()

        # Валидация
        if not title or not description or not price or not category:
            return "Все поля обязательны для заполнения", 400

        try:
            price = int(price)
        except ValueError:
            return "Цена должна быть числом", 400

        # Загружаем существующие объявления
        ads = load_ads()

        # Создаем новое объявление
        new_id = max([ad['id'] for ad in ads]) + 1 if ads else 1

        new_ad = {
            'id': new_id,
            'title': title,
            'description': description,
            'price': price,
            'category': category,
            'created_at': datetime.now().isoformat()
        }

        ads.append(new_ad)
        save_ads(ads)

        return redirect(url_for('index'))

    return render_template('add_ad.html')


@app.route('/delete/<int:ad_id>')
def delete_ad(ad_id):
    ads = load_ads()
    ads = [ad for ad in ads if ad['id'] != ad_id]
    save_ads(ads)
    return redirect(url_for('index'))


@app.route('/edit/<int:ad_id>', methods=['GET', 'POST'])
def edit_ad(ad_id):
    ads = load_ads()
    ad = next((a for a in ads if a['id'] == ad_id), None)

    if not ad:
        return "Объявление не найдено", 404

    if request.method == 'POST':
        # Обновляем данные
        ad['title'] = request.form.get('title', '').strip()
        ad['description'] = request.form.get('description', '').strip()
        ad['price'] = int(request.form.get('price', 0))
        ad['category'] = request.form.get('category', '').strip()

        save_ads(ads)
        return redirect(url_for('index'))

    return render_template('edit_ad.html', ad=ad)


if __name__ == '__main__':
    app.run(debug=True)