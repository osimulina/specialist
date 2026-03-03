import random
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).parent
path_to_db = BASE_DIR / "store.db"

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def get_unique_id(dct):
    ids = [i['id'] for i in dct]
    unique_id = sorted(ids)[-1] + 1
    return unique_id

# quotes = [
#    {
#        "rating": 1,
#        "id": 3,
#        "author": "Rick Cook",
#        "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
#    },
#    {
#        "rating": 1,
#        "id": 5,
#        "author": "Waldi Ravens",
#        "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
#    },
#    {
#        "rating": 1,
#        "id": 6,
#        "author": "Mosher’s Law of Software Engineering",
#        "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
#    },
#    {
#        "rating": 1,
#        "id": 8,
#        "author": "Yoggi Berra",
#        "text": "В теории, теория и практика неразделимы. На практике это не так."
#    },

# ]

@app.route("/")
def hello_world():
    return jsonify(data="Hello, World!")

@app.route("/quotes")
def get_all_quotes():
    select_quotes = "SELECT * from quotes"
    connection = sqlite3.connect("store.db")
    cursor = connection.cursor()
    cursor.execute(select_quotes)
    quotes_db = cursor.fetchall()
    cursor.close()
    connection.close()
    keys = ('id', 'author', 'text')
    quotes = [] 
    for line in quotes_db:
        quote = dict(zip(keys, line))
        quotes.append(quote)
    return jsonify(quotes), 200

# Практика Часть 2 Дополнительно
@app.route("/quotes/filter")
def get_filtered_quotes():
    filter = request.args.to_dict()
    filtered_quotes = []
    for quote in quotes:
        if all([str(quote.get(key)) == value for key, value in filter.items()]):
            filtered_quotes.append(quote)
    return jsonify(filtered_quotes), 200


# Задание 1-(1-2)
@app.route("/quotes/<int:id>")
def get_quote(id):
    for quote in quotes: 
        if quote['id'] == id:
            return quote
    return jsonify(data=f"Quote with id={id} not found"), 404

# Задание 1-3
@app.route("/quotes/count")
def count_quotes():
    return jsonify({"count": len(quotes)})

# Задание 1-4
@app.route("/quotes/random")
def get_random_quote():
    random_quote = random.choice(quotes)
    return jsonify(random_quote)

# Практика Часть 2    
@app.route("/quotes", methods=['POST'])
def create_quote():
    new_quote = request.json
    unique_id = get_unique_id(quotes)
    new_quote['id'] = unique_id
    if not 'rating' in new_quote.keys():
        new_quote['rating'] = 1
    quotes.append(new_quote)
    return jsonify(new_quote), 201

# Практика Часть 2   
@app.route("/quotes/<int:id>", methods=['DELETE'])
def delete_quote(id):
    for quote in quotes: 
        if quote['id'] == id:
            quotes.remove(quote)
            return jsonify(message=f"Quote with id={id} is deleted"), 200
    return jsonify(message=f"Quote with id={id} not found"), 404

# Практика Часть 2   
@app.route("/quotes/<int:id>", methods=['PUT'])
def edit_quote(id):
    new_quote = request.json
    for quote in quotes: 
        if quote['id'] == id:
            for key, value in new_quote.items():
                quote[key] = value
            if quote['rating'] > 5:
                quote['rating'] = 1
            return jsonify(quote), 200
    return jsonify(message=f"Quote with id={id} not found"), 404

if __name__ == "__main__":
    app.run(debug=True)

