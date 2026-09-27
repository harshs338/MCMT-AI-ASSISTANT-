from flask import Blueprint, render_template


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/login")
def login():
    return render_template("login.html")


@main.route("/register")
def register():
    return render_template("register.html")


@main.route("/chat")
def chat():
    return render_template("chat.html")


@main.route("/student-chat")
def student_chat():
    return render_template("student_chat.html")


@main.route("/profile")
def profile():
    return render_template("profile.html")


@main.route("/notices")
def notices():
    return render_template("notices.html")