from flask import Flask, request, render_template_string, g, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "dev-secret-key-not-for-production"
DB_PATH = os.path.join(os.path.dirname(__file__), "mininotes.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            text TEXT NOT NULL
        )
    """)
    conn.execute("INSERT INTO users (username, password) VALUES ('admin', 'S3cr3tAdminPass!')")
    conn.execute("INSERT INTO users (username, password) VALUES ('alice', 'alice123')")
    conn.commit()
    conn.close()


LOGIN_PAGE = """
<h2>MiniNotes - вход</h2>
<form method="post">
  Логин: <input name="username"><br>
  Пароль: <input name="password" type="password"><br>
  <button type="submit">Войти</button>
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
"""

NOTES_PAGE = """
<h2>Заметки пользователя {{ user }}</h2>
<form method="post">
  <textarea name="text" rows="3" cols="40"></textarea><br>
  <button type="submit">Добавить заметку</button>
</form>
<ul>
{% for n in notes %}
  <li><b>{{ n[0] }}:</b> {{ n[1]|safe }}</li>
{% endfor %}
</ul>
<a href="/logout">Выйти</a>
"""


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        query = (
            "SELECT username FROM users WHERE username='"
            + username
            + "' AND password='"
            + password
            + "'"
        )
        db = get_db()
        cur = db.execute(query)
        row = cur.fetchone()

        if row:
            session["user"] = row[0]
            return redirect("/notes")
        else:
            error = "Неверный логин или пароль"
    return render_template_string(LOGIN_PAGE, error=error)


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    if request.method == "POST":
        text = request.form.get("text", "")
        db.execute(
            "INSERT INTO notes (author, text) VALUES (?, ?)",
            (session["user"], text),
        )
        db.commit()
    rows = db.execute("SELECT author, text FROM notes").fetchall()
    return render_template_string(NOTES_PAGE, user=session["user"], notes=rows)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    init_db()
    print("БД инициализирована. Тестовые пользователи: admin/S3cr3tAdminPass!, alice/alice123")
    app.run(host="127.0.0.1", port=5000, debug=True)
