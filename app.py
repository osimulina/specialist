from pathlib import Path
import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, func, DateTime
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
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True, unique=True)
    surname: Mapped[str] = mapped_column(
        String(32), index=True, nullable=True, unique=True
    )
    is_deleted: Mapped[str] = mapped_column(
        String(10), nullable=True, default=None, server_default=None
    )
    quotes: Mapped[list["QuoteModel"]] = relationship(
        back_populates="author", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __init__(self, name, surname):
        self.name = name
        self.surname = surname

    def to_dict(self):
        
        return {"id": self.id, "name": self.name, "surname": self.surname}


class QuoteModel(db.Model):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["AuthorModel"] = relationship(back_populates="quotes")
    text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(
        default=1, server_default=str(1), nullable=False
    )
    is_deleted: Mapped[str] = mapped_column(
        String(10), nullable=True, default="", server_default=""
    )
    created: Mapped[datetime.datetime] = mapped_column(DateTime(), server_default=func.now())

    def __init__(self, author, text, rating=1):
        self.author = author
        self.text = text
        self.rating = rating

    def to_dict(self):
        return {"id": self.id, "text": self.text, "rating": self.rating, "created": self.created.strftime('%d.%m.%Y')}

def is_object_valid(obj: QuoteModel | AuthorModel | None) -> bool:
    if not obj or obj.is_deleted == 'Удалено':
        return False
    else:
        return True

@app.route("/")
def hello_world():
    return jsonify(data="Hello, World!")


@app.route("/authors")
def get_authors():
    """Вывод данных всех авторов"""

    allowed_parameters = {"surname": AuthorModel.surname, "name": AuthorModel.name}
    sort_parameters = request.args.getlist("sort_by")
    sort_by = []
    for param in sort_parameters:
        if param in allowed_parameters.keys():
            sort_by.append(allowed_parameters[param])
        else:
            return jsonify(authors="Wrong attribute"), 404
    authors = db.session.scalars(db.select(AuthorModel).where(AuthorModel.is_deleted!='Удалено').order_by(*sort_by))
    return jsonify(authors=[author.to_dict() for author in authors]), 200

@app.route("/authors/deleted")
def get_deleted_authors():
    """Вывод всех удаленных авторов"""

    allowed_parameters = {"surname": AuthorModel.surname, "name": AuthorModel.name}
    sort_parameters = request.args.getlist("sort_by")
    sort_by = []
    for param in sort_parameters:
        if param in allowed_parameters.keys():
            sort_by.append(allowed_parameters[param])
        else:
            return jsonify(authors="Wrong attribute"), 404
    authors = db.session.scalars(db.select(AuthorModel).where(AuthorModel.is_deleted=='Удалено').order_by(*sort_by))
    return jsonify(authors=[author.to_dict() for author in authors]), 200

@app.route("/authors/restore")
def restore_deleted_authors():
    """Восстановление данных авторов"""

    authors = db.session.scalars(db.select(AuthorModel).where(AuthorModel.is_deleted=='Удалено')).all()
    authors_copy = [author.to_dict() for author in authors]
    if not authors:
        return jsonify(message='Нет удаленных пользователей'), 200
    for author in authors:
        author.is_deleted = None
        for quote in author.quotes:
            quote.is_deleted = None
    db.session.commit()
    return jsonify(authors=authors_copy), 200

@app.route("/authors/<int:author_id>")
def get_author(author_id):
    """Вывод данных автора по id"""

    author = db.session.get(AuthorModel, author_id)
    if not is_object_valid(author):
        return jsonify(message=f"Author with {author_id} not found"), 404
    return jsonify(author.to_dict()), 200


@app.route("/authors", methods=["POST"])
def create_author():
    """Создание данных нового автора"""

    try:
        author_data = request.json
        author_data_check = set(author_data.keys()) - {"name", "surname"}
        for i in author_data_check:
            author_data.pop(i)
        new_author = AuthorModel(**author_data)
        db.session.add(new_author)
        db.session.commit()
        return (
            jsonify(new_author.to_dict()),
            201,
        )
    except IntegrityError:
        return (
            jsonify(
                error="New author with this name is already created. Choose another one"
            ),
            400,
        )


@app.route("/authors/<int:author_id>", methods=["PUT"])
def edit_author(author_id):
    """Редактирование данных автора"""

    author_data = request.json
    attrs = set(author_data.keys()) & {"name"}
    author = db.session.get(AuthorModel, author_id)
    if not is_object_valid(author):
        return jsonify(message=f"Author with id={author_id} not found"), 404
    for attr in attrs:
        setattr(author, attr, author_data[attr])
    db.session.commit()
    return jsonify(author.to_dict()), 201


@app.route("/authors/<int:author_id>", methods=["DELETE"])
def delete_author(author_id):
    """Удаление данных автора"""
    
    author = db.session.get(AuthorModel, author_id)
    if not is_object_valid(author):
        return jsonify(message=f"Author with id={author_id} not found"), 404
    author.is_deleted = 'Удалено'
    for quote in author.quotes:
        quote.is_deleted = 'Удалено'
    db.session.commit()
    return jsonify(message=f"Author with id={author_id} is deleted"), 200


@app.route("/quotes/")
def get_quotes():
    """Вывод всех цитат"""

    quotes = db.session.scalars(db.select(QuoteModel).where((QuoteModel.is_deleted == None) | (QuoteModel.is_deleted!='Удалено')))
    return jsonify(quotes=[quote.to_dict() for quote in quotes]), 200


@app.route("/quotes/<int:quote_id>")
def get_quote(quote_id):
    """Выбор цитаты по id"""

    quote = db.session.get(QuoteModel, quote_id)
    if not is_object_valid(quote):
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    else:
        return jsonify(quote.to_dict()), 200


@app.route("/authors/<int:author_id>/quotes")
def get_author_quotes(author_id):
    """Вывод всех цитат автора"""

    author = db.session.get(AuthorModel, author_id)
    quotes = []
    if not is_object_valid(author):
        return jsonify(message=f"Author with id={author_id} not found"), 200
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
    q = QuoteModel(
        author,
        new_quote["text"],
    )
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
        return jsonify(message=f"Quotes by {filter} not found"), 404


@app.route("/quotes/<int:quote_id>", methods=["PUT"])
def edit_quote(quote_id):
    """Редактирование цитаты"""

    new_quote = request.json
    attrs = set(new_quote.keys()) & {"author", "text", "rating"}
    if "rating" in new_quote and not new_quote["rating"] in range(1, 6):
        new_quote["rating"] = 1
    quote = db.session.get(QuoteModel, quote_id)
    if not is_object_valid(quote):
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
    if not any([rate_edit == "decr", rate_edit == "incr"]):
        return jsonify(message="Wrong query parameter"), 400
    if not is_object_valid(quote):
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    if rate_edit == "incr" and new_rating < 5:
        new_rating += 1
    elif rate_edit == "decr" and new_rating > 1:
        new_rating -= 1
    quote.rating = new_rating
    db.session.commit()
    return jsonify(quote.to_dict()), 201


@app.route("/quotes/<int:quote_id>", methods=["DELETE"])
def delete_quote(quote_id):
    """Удаление цитаты"""

    quote = db.session.get(QuoteModel, quote_id)
    if not is_object_valid(quote):
        return jsonify(message=f"Quote with id={quote_id} not found"), 404
    db.session.delete(quote)
    db.session.commit()
    return jsonify(message=f"Quote with id={quote_id} is deleted"), 200


if __name__ == "__main__":
    app.run(debug=True)
