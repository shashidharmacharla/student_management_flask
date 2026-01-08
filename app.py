from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import csv

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to a strong secret key

DATABASE = "students.db"

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Simple admin credentials (for demo purposes)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

# Email regex for validation
EMAIL_REGEX = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

# DB connection helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_email(email):
    return re.match(EMAIL_REGEX, email)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = User(username)
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    search_query = request.args.get("search", "").strip()
    conn = get_db_connection()
    if search_query:
        query = """
        SELECT * FROM students
        WHERE name LIKE ? OR roll LIKE ? OR email LIKE ? OR course LIKE ?
        """
        like_query = f"%{search_query}%"
        students = conn.execute(query, (like_query, like_query, like_query, like_query)).fetchall()
    else:
        students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("index.html", students=students, search_query=search_query)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        name = request.form["name"].strip()
        roll = request.form["roll"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()

        if not (name and roll and email and course):
            flash("All fields are required.", "danger")
        elif not is_valid_email(email):
            flash("Invalid email format.", "danger")
        else:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO students (name, roll, email, course) VALUES (?, ?, ?, ?)",
                (name, roll, email, course),
            )
            conn.commit()
            conn.close()
            flash("Student added successfully!", "success")
            return redirect(url_for("index"))

    return render_template("add_student.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?", (id,)
    ).fetchone()

    if request.method == "POST":
        name = request.form["name"].strip()
        roll = request.form["roll"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()

        if not (name and roll and email and course):
            flash("All fields are required.", "danger")
        elif not is_valid_email(email):
            flash("Invalid email format.", "danger")
        else:
            conn.execute(
                "UPDATE students SET name=?, roll=?, email=?, course=? WHERE id=?",
                (name, roll, email, course, id),
            )
            conn.commit()
            conn.close()
            flash("Student updated successfully!", "success")
            return redirect(url_for("index"))

    conn.close()
    return render_template("edit_student.html", student=student)

@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    data = conn.execute("SELECT course, COUNT(*) as count FROM students GROUP BY course").fetchall()
    conn.close()

    courses = [row["course"] for row in data]
    counts = [row["count"] for row in data]

    return render_template("dashboard.html", courses=courses, counts=counts)

@app.route("/export_csv")
@login_required
def export_csv():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    def generate():
        header = ["ID", "Name", "Roll No", "Email", "Course"]
        yield ",".join(header) + "\n"

        for student in students:
            row = [str(student["id"]), student["name"], student["roll"], student["email"], student["course"]]
            yield ",".join(row) + "\n"

    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=students.csv"})

if __name__ == "__main__":
    app.run(debug=True)


