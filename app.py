
from flask import Flask, render_template, request, redirect, session
import psycopg
import os
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

# Local demonstration: credentials are stored in server memory.
active_logins = {}

def connect():
    token = session.get("token")
    username, password = active_logins[token]

    return psycopg.connect(
        host="localhost",
        dbname="library_db",
        user=username,
        password=password,
        port=5432
    )

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = session.get("token")
        if not token or token not in active_logins:
            session.clear()
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper

# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            with psycopg.connect(
                host="localhost",
                dbname="library_db",
                user=username,
                password=password,
                port=5432
            ):
                pass

            session.clear()
            token = secrets.token_hex(32)
            active_logins[token] = (username, password)
            session["token"] = token
            return redirect("/")

        except psycopg.OperationalError:
            error = "Invalid login or database unavailable"

    return render_template("login.html", error=error)

# VIEW BOOKS
@app.route("/")
@login_required
def home():
    with connect() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM books ORDER BY id")
            books = cur.fetchall()

    return render_template("index.html", books=books)

# ADD BOOK
@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form["title"]
    author = request.form["author"]
    price = request.form["price"]

    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO books (title, author, price) VALUES (%s, %s, %s)",
                (title, author, price)
            )

    return redirect("/")

# UPDATE BOOK
@app.route("/update/<int:id>", methods=["POST"])
@login_required
def update(id):
    price = request.form["price"]

    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "UPDATE books SET price=%s WHERE id=%s",
                (price, id)
            )

    return redirect("/")

# DELETE BOOK
@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    with connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "DELETE FROM books WHERE id=%s",
                (id,)
            )

    return redirect("/")

# LOGOUT
@app.route("/logout", methods=["POST"])
def logout():
    token = session.pop("token", None)
    active_logins.pop(token, None)
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=False)
