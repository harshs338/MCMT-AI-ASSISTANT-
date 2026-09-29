from flask import Blueprint, render_template, request, session, redirect, url_for
from sqlite3 import IntegrityError
from werkzeug.security import generate_password_hash
from database.database import get_db_connection


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            return render_template(
                "login.html",
                error="Email and password are required."
            )

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user is None:
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        from werkzeug.security import check_password_hash

        if not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]

        return redirect(url_for("main.student_chat"))

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        student_id = request.form["student_id"]
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        if not student_id or not name or not email or not phone or not password:
            return render_template(
                "register.html",
                error="All fields are required."
            )

        password_hash = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO users
                (student_id, name, email, phone, password_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (student_id, name, email, phone, password_hash)
            )

            connection.commit()

        except IntegrityError:
            return render_template(
                "register.html",
                error="Student ID or Email already exists."
            )

        finally:
            connection.close()

        return render_template(
            "register.html",
            success="Registration successful!"
        )

    return render_template("register.html")


@main.route("/chat")
def chat():
    return render_template("chat.html")


@main.route("/student-chat")
def student_chat():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    return render_template("student_chat.html")

@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))


@main.route("/profile")
def profile():
    return render_template("profile.html")


@main.route("/notices")
def notices():
    return render_template("notices.html")