from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecret"

DB_NAME = "quiz.db"

# ---------- Database Setup ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                score INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

# ---------- Routes ----------
@app.before_request
def before_request():
    g.user = None
    if "user_id" in session:
        g.user = session["user_id"]

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already taken!"
        finally:
            conn.close()
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("quiz"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    questions = [
        {"q": "What does CPU stand for?", "options": ["Central Processing Unit", "Computer Personal Unit", "Central Process Utility", "Control Processing Unit"], "answer": 1},
        {"q": "What is the capital of France?", "options": ["Berlin", "Paris", "Madrid", "Rome"], "answer": 2},
        {"q": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter", "Venus"], "answer": 2}
    ]

    if request.method == "POST":
        score = 0
        for i, question in enumerate(questions, start=1):
            if request.form.get(f"q{i}") == str(question["answer"]):
                score += 1

        conn = get_db()
        conn.execute("UPDATE users SET score=? WHERE id=?", (score, session["user_id"]))
        conn.commit()
        conn.close()

        return redirect(url_for("result", score=score))

    return render_template("quiz.html", questions=questions)

@app.route("/result")
def result():
    score = request.args.get("score", type=int)
    return render_template("result.html", score=score)

@app.route("/leaderboard")
def leaderboard():
    conn = get_db()
    leaders = conn.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT 10").fetchall()
    conn.close()
    return render_template("leaderboard.html", leaders=leaders)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
