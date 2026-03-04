from pathlib import Path
import random

from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey
from flask_migrate import Migrate


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
    rating: Mapped[int] = mapped_column(default=1)

    def __init__(self, author, text):
        self.author = author
        self.text  = text

    def to_dict(self):
        return {"id": self.id,
                "text": self.text,
                "rating": self.rating}



@app.route("/")
def hello_world():
    return jsonify(data="Hello, World!")


@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id):
    """Вывод всех цитат"""
    author = db.session.get(AuthorModel, author_id)
    quotes =[]
    for quote in author.quotes:
        quotes.append(quote.to_dict())
    return jsonify(author=author.name, quotes=quotes), 200


@app.route("/quotes/filter")
def get_filtered_quotes():
    """Фильтрация цитат"""
    if request.args:
        quotes = db.session.query(QuoteModel).filter_by(**request.args).all()
        quotes = [quote.to_dict() for quote in quotes]
        return jsonify(quotes), 200
    else:
        return jsonify(message=f'Quotes by {filter} not found'), 404


@app.route("/quotes/<int:id>")
def get_quote(id):
    """Выбор цитаты по id"""

    quote = db.session.get(QuoteModel, id)
    if not quote:
        return jsonify(message=f"Quote with id={id} not found"), 404
    else:
        return jsonify(quote.to_dict()), 200

  
@app.route("/quotes/count")
def count_quotes():
    """Количество цитат"""

    count = len(db.session.scalars(db.select(QuoteModel)).all())
    if count:
        return jsonify(count=count)
    abort(503)


@app.route("/quotes/random")
def get_random_quote():
    """Cлучаный выбор цитаты"""

    random_quote = random.choice(db.session.scalars(db.select(QuoteModel)).all())
    return jsonify(random_quote.to_dict())

@app.route("/quotes", methods=["POST"])
def create_quote():
    """Создание новой цитаты"""

    new_quote = request.json
    author = str(new_quote.get("author", "Unknown"))
    text = str(new_quote.get("text", ""))
    rating = int(new_quote.get("rating", 1))
    if rating > 5:
        rating = 1
    quote = QuoteModel(author=author,
                       text=text,
                       rating=rating)
    db.session.add(quote)
    db.session.commit()
    return (
        jsonify(quote.to_dict()),
        201,
    )


@app.route("/quotes/<int:id>", methods=["DELETE"])
def delete_quote(id):
    """Удаление цитаты"""

    quote = db.session.get(QuoteModel, id)
    if not quote: 
        return jsonify(message=f"Quote with id={id} not found"), 404
    db.session.delete(quote)
    db.session.commit()
    return jsonify(message=f"Quote with id={id} is deleted"), 200



@app.route("/quotes/<int:id>", methods=["PUT"])
def edit_quote(id):
    """Редактирование цитаты"""
    
    new_quote = request.json
    attrs = set(new_quote.keys()) & {"author", "text", "rating"}
    if "rating" in new_quote and new_quote["rating"] > 5:
        new_quote["rating"] = 1
    quote = db.session.get(QuoteModel, id)
    if not quote: 
        return jsonify(message=f"Quote with id={id} not found"), 404
    for attr in attrs:
        setattr(quote, attr, new_quote[attr])
    db.session.commit()
    return jsonify(quote.to_dict()), 201


if __name__ == "__main__":
    app.run(debug=True)
