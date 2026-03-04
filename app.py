from pathlib import Path
import random

from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError


BASE_DIR = Path(__file__).parent

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'quotes.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)

class AuthorModel(db.Model):
    __tablename__ = 'authors'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int] = mapped_column(String(32), index= True, unique=True)
    quotes: Mapped[list['QuoteModel']] = relationship( back_populates='author', lazy='dynamic')

    def __init__(self, name):
       self.name = name

    def to_dict(self):
        return {"name": self.name}


class QuoteModel(db.Model):
    __tablename__ = 'quotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('authors.id'))
    author: Mapped['AuthorModel'] = relationship(back_populates='quotes')
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(default=1, server_default=str(1))

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text  = text
        self.rating = rating

    def to_dict(self):
        return {"id": self.id,
                "text": self.text,
                "rating": self.rating}



@app.route("/")
def hello_world():
    return jsonify(data="Hello, World!")

@app.route("/authors")
def get_authors():
    """Вывод данных всех авторов"""

    authors = db.session.scalars(db.select(AuthorModel))
    return jsonify(authors=[author.to_dict() for author in authors]), 200

@app.route("/authors/<int:author_id>")
def get_author(author_id):

    """Вывод данных автора по id"""
    author = db.session.get(AuthorModel, author_id)
    return jsonify(author.to_dict()), 200

@app.route("/authors", methods=["POST"])
def create_author():
    """Создание данных нового автора"""
    try:
        author_data = request.json
        new_author = AuthorModel(author_data["name"])
        db.session.add(new_author)
        db.session.commit()
        return (
        jsonify(new_author.to_dict()),
        201,
    )
    except IntegrityError:
        return (
        jsonify(error="New author with this name is already created. Choose another one"),
        503,
    )
        
@app.route("/authors/<int:author_id>", methods=["PUT"])
def edit_author(author_id):
    """Редактирование данных автора"""
    
    author_data = request.json
    attrs = set(author_data.keys()) & {"name"}
    author = db.session.get(AuthorModel, author_id)
    if not author: 
        return jsonify(message=f"Author with id={author_id} not found"), 404
    for attr in attrs:
        setattr(author, attr, author_data[attr])
    db.session.commit()
    return jsonify(author.to_dict()), 201


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    """Удаление данных автора"""

    author = db.session.get(AuthorModel, author_id)
    if not author: 
        return jsonify(message=f"Author with id={author_id} not found"), 404
    db.session.delete(author)
    db.session.commit()
    return jsonify(message=f"Author with id={author_id} is deleted"), 200

@app.route("/quotes/")
def get_quotes():
    """Вывод всех цитат"""
    quotes = db.session.scalars(db.select(QuoteModel))
    return jsonify(quotes=[quote.to_dict() for quote in quotes]), 200

@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id):
    """Выбор цитаты по id"""

    quote = db.session.get(QuoteModel, quote_id)
    if not quote:
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    else:
        return jsonify(quote.to_dict()), 200


@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id):
    """Вывод всех цитат автора"""
    author = db.session.get(AuthorModel, author_id)
    quotes =[]
    for quote in author.quotes:
        quotes.append(quote.to_dict())
    return jsonify(author=author.name, quotes=quotes), 200

@app.route("/authors/<int:author_id>/quotes", methods=["POST"])
def get_create_author_quote(author_id):
    """Пост новой цитаты автора"""

    author = db.session.get(AuthorModel, author_id)
    new_quote = request.json
    if "rating" in new_quote and not new_quote["rating"] in range(1, 6):
        new_quote["rating"] = 1
    q = QuoteModel(author, new_quote["text"],)
    db.session.add(q)
    db.session.commit()
    return jsonify(q.to_dict()), 200



@app.route("/quotes/filter")
def get_filtered_quotes():
    """Фильтрация цитат"""
    if request.args:
        quotes = db.session.query(QuoteModel).filter_by(**request.args).all()
        quotes = [quote.to_dict() for quote in quotes]
        return jsonify(quotes), 200
    else:
        return jsonify(message=f'Quotes by {filter} not found'), 404


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_quote(quote_id):
    """Редактирование цитаты"""
    
    new_quote = request.json
    attrs = set(new_quote.keys()) & {"author", "text", "rating"}
    if "rating" in new_quote and not new_quote["rating"] in range(1, 6):
        new_quote["rating"] = 1
    quote = db.session.get(QuoteModel, quote_id)
    if not quote: 
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    for attr in attrs:
        setattr(quote, attr, new_quote[attr])
    db.session.commit()
    return jsonify(quote.to_dict()), 201

@app.route("/quotes/<int:quote_id>/<rate_edit>", methods=["PUT"])
def edit_quote_rating(quote_id, rate_edit):
    """Редактирование рейтинга цитаты"""
    
    quote = db.session.get(QuoteModel, quote_id)
    new_rating = quote.rating
    if not any([rate_edit == 'decr', rate_edit == 'incr']):
        return jsonify(message='Wrong rate_edit'), 400
    if not quote: 
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    if rate_edit == 'incr' and new_rating < 5:
        new_rating += 1
    elif rate_edit == 'decr' and new_rating > 1:
        new_rating -= 1
    quote.rating = new_rating
    db.session.commit()
    return jsonify(quote.to_dict()), 201
  
# @app.route("/quotes/count")
# def count_quotes():
#     """Количество цитат"""

#     count = len(db.session.scalars(db.select(QuoteModel)).all())
#     if count:
#         return jsonify(count=count)
#     abort(503)


# @app.route("/quotes/random")
# def get_random_quote():
#     """Cлучаный выбор цитаты"""

#     random_quote = random.choice(db.session.scalars(db.select(QuoteModel)).all())
#     return jsonify(random_quote.to_dict())

# @app.route("/quotes", methods=["POST"])
# def create_quote():
#     """Создание новой цитаты"""

#     new_quote = request.json
#     author = str(new_quote.get("author", "Unknown"))
#     text = str(new_quote.get("text", ""))
#     rating = int(new_quote.get("rating", 1))
#     if rating > 5:
#         rating = 1
#     quote = QuoteModel(author=author,
#                        text=text,
#                        rating=rating)
#     db.session.add(quote)
#     db.session.commit()
#     return (
#         jsonify(quote.to_dict()),
#         201,
#     )


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
    """Удаление цитаты"""

    quote = db.session.get(QuoteModel, quote_id)
    if not quote: 
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    db.session.delete(quote)
    db.session.commit()
    return jsonify(message=f"Quote with id={quote_id} is deleted"), 200






if __name__ == "__main__":
    app.run(debug=True)
