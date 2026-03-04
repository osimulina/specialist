from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request, g, abort

BASE_DIR = Path(__file__).parent
DATABASE = "store.db"


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
path_to_db = BASE_DIR / "store.db"


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = make_dicts
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().cursor().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def get_unique_id(dct):
    ids = [i["id"] for i in dct]
    unique_id = sorted(ids)[-1] + 1
    return unique_id


@app.route("/")
def hello_world():
    return jsonify(data="Hello, World!")


@app.route("/quotes")
def get_all_quotes():
    select_quotes = "SELECT * from quotes"
    quotes_db = query_db(select_quotes)
    return jsonify(quotes_db), 200


# Практика Часть 2 Дополнительно
@app.route("/quotes/filter")
def get_filtered_quotes():
    filters = request.args.to_dict()
    query = "SELECT * FROM quotes WHERE 1=1"
    values = []
    allowed_fields = ['id', 'author', 'text', 'rating']
    for key, value in filters.items():
        if key in allowed_fields:
            query += " AND {} = ?".format(key)  
            values.append(value)              
    quotes_db = query_db(query, values)
    return jsonify(quotes_db), 200


# Задание 1-(1-2)
@app.route("/quotes/<int:id>")
def get_quote(id):
    db = get_db()
    cursor = db.cursor()
    select_quotes = "SELECT * from quotes WHERE id=?"
    quotes_db = cursor.execute(select_quotes, (str(id),)).fetchone()
    print(quotes_db)
    if quotes_db:
        return jsonify(quotes_db)
    else:
        return jsonify(data=f"Quote with id={id} not found"), 404
    


# Задание 1-3
@app.route("/quotes/count")
def count_quotes():
    db = get_db()
    cursor = db.cursor()
    count_query = "SELECT COUNT (*) as count FROM quotes"
    count = cursor.execute(count_query).fetchone()
    if count:
        return jsonify(count)
    abort(503)


# Задание 1-4
@app.route("/quotes/random")
def get_random_quote():
    random_quote = query_db("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1")
    return jsonify(random_quote)


# Практика Часть 2
@app.route("/quotes", methods=["POST"])
def create_quote():
    new_quote = request.json

    author = str(new_quote.get('author', 'Unknown'))
    text = str(new_quote.get('text', ''))
    rating = int(new_quote.get('rating', 1))
    if rating > 5:
        rating = 1
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"INSERT INTO quotes (author, text, rating) VALUES (?, ?, ?);", 
                   (author, text, rating))
    db.commit()
    unique_id = cursor.lastrowid
    return jsonify({
        "id": unique_id,
        "author": author,
        "text": text,
        "rating": rating
    }), 201


# Практика Часть 2
@app.route("/quotes/<int:id>", methods=["DELETE"])
def delete_quote(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM quotes WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        return jsonify(message=f"Quote with id={id} not found"), 404
    db.commit()
    return jsonify(message=f"Quote with id={id} is deleted"), 200


# Практика Часть 2
@app.route("/quotes/<int:id>", methods=["PUT"])
def edit_quote(id):
    new_quote = request.json
    db = get_db()
    cursor = db.cursor()
    attrs = set(new_quote.keys()) & {'author', 'text', 'rating'}
    if 'rating' in new_quote and new_quote['rating'] > 5:
        new_quote['rating'] = 1
    query = f"UPDATE quotes SET {', '.join([attr + '=?' for attr in attrs])} WHERE id=?;"
    cursor.execute(query, (tuple([new_quote[attr] for attr in attrs])+(id, )))   
    
    if cursor.rowcount == 0:
        return jsonify(message=f"Quote with id={id} not found"), 404
    db.commit()
    new_quote = query_db("SELECT * FROM quotes WHERE id = ?", (str(id),))
    return jsonify(new_quote), 201


if __name__ == "__main__":
    app.run(debug=True)
