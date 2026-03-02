import random

from flask import Flask

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

quotes = [
   {
       "id": 3,
       "author": "Rick Cook",
       "text": "Программирование сегодня — это гонка разработчиков программ, стремящихся писать программы с большей и лучшей идиотоустойчивостью, и вселенной, которая пытается создать больше отборных идиотов. Пока вселенная побеждает."
   },
   {
       "id": 5,
       "author": "Waldi Ravens",
       "text": "Программирование на С похоже на быстрые танцы на только что отполированном полу людей с острыми бритвами в руках."
   },
   {
       "id": 6,
       "author": "Mosher’s Law of Software Engineering",
       "text": "Не волнуйтесь, если что-то не работает. Если бы всё работало, вас бы уволили."
   },
   {
       "id": 8,
       "author": "Yoggi Berra",
       "text": "В теории, теория и практика неразделимы. На практике это не так."
   },

]

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/quotes")
def get_all_quotes():
    return quotes

# Задание 1-2
@app.route("/quotes/<int:id>")
def get_quote(id):
    for quote in quotes: 
        if quote['id'] == id:
            return quote
    return f"Quote with id={id} not found", 404

# Задание 3
@app.route("/quotes/count")
def count_quotes():
    return {"count": len(quotes)}

# Задание 4
@app.route("/quotes/random")
def get_random_quote():
    random_quote = random.choice(quotes)
    return random_quote
    

if __name__ == "__main__":
    app.run(debug=True)

