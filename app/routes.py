from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from google import genai
from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from werkzeug.security import generate_password_hash
from database.database import get_db_connection


main = Blueprint("main", __name__)

client = genai.Client()

def format_time(timestamp):
    time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    time = time + timedelta(hours=5, minutes=30)

    return time.strftime("%I:%M %p").lstrip("0")

def get_ai_response(message):
    instructions = """
You are MCMT AI Assistant, a helpful college assistant.

Your most important rule is to match the language of the student's question.

LANGUAGE RULES:
1. If the question is written in English, answer completely in English.
2. If the question is written in Roman Hinglish, answer completely in Roman Hinglish.
3. If the question contains both English and Roman Hinglish, use the same mixed style.
4. Do not convert an English question into Hindi or Roman Hinglish.
5. Do not convert a Roman Hinglish question into English.
6. For short questions like "What is BCA?", "What is MCA?", or "What is admission?",
   identify the language from the wording of the question and answer in that language.

Keep answers simple, clear, and student-friendly.

Do not make up college-specific information.
If you do not have enough information to answer a college-specific question,
say that the information is not currently available.

Student question:
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=instructions + message
        )

        return response.text

    except Exception:
        return "Sorry, I am unable to respond right now. Please try again later."


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

    chat_id = request.args.get("chat_id")

    connection = get_db_connection()

    chats = connection.execute(
        """
        SELECT chat_id, title, created_at
        FROM chats
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    selected_chat = None
    messages = []

    if chat_id:
        selected_chat = connection.execute(
            """
            SELECT chat_id, title
            FROM chats
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, session["user_id"])
        ).fetchone()

        if selected_chat:
            messages = connection.execute(
                """
                SELECT sender, content, created_at
                FROM messages
                WHERE chat_id = ?
                ORDER BY created_at ASC, message_id ASC
                """,
                (selected_chat["chat_id"],)
            ).fetchall()

        messages = [
        {
            "sender": message["sender"],
            "content": message["content"],
            "created_at": format_time(message["created_at"])
        }
        for message in messages
    ]    

    connection.close()

    return render_template(
        "student_chat.html",
        chats=chats,
        selected_chat=selected_chat,
        messages=messages
    )

@main.route("/send-message", methods=["POST"])
def send_message():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    chat_id = request.form["chat_id"]
    content = request.form["content"]

    if not content.strip():
        return redirect(
            url_for("main.student_chat", chat_id=chat_id)
        )

    connection = get_db_connection()

    chat = connection.execute(
        """
        SELECT chat_id
        FROM chats
        WHERE chat_id = ? AND user_id = ?
        """,
        (chat_id, session["user_id"])
    ).fetchone()

    if chat is None:
        connection.close()
        return redirect(url_for("main.student_chat"))

    message_count = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM messages
        WHERE chat_id = ?
        """,
        (chat_id,)
    ).fetchone()

    connection.execute(
        """
        INSERT INTO messages (chat_id, sender, content)
        VALUES (?, ?, ?)
        """,
        (chat_id, "user", content.strip())
    )

    if message_count["total"] == 0:

        title = content.strip()

        if len(title) > 30:
            title = title[:30] + "..."

        connection.execute(
            """
            UPDATE chats
            SET title = ?
            WHERE chat_id = ? AND user_id = ?
            """,
            (title, chat_id, session["user_id"])
        )

    ai_response = get_ai_response(content.strip())

    connection.execute(
        """
        INSERT INTO messages (chat_id, sender, content)
        VALUES (?, ?, ?)
        """,
        (chat_id, "ai", ai_response)
    )

    connection.commit()
    connection.close()

    return jsonify({
    "success": True,
    "user_message": content.strip(),
    "ai_response": ai_response
    })

@main.route("/new-chat")
def new_chat():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO chats (user_id, title)
        VALUES (?, ?)
        """,
        (session["user_id"], "New Chat")
    )

    connection.commit()

    chat_id = cursor.lastrowid

    connection.close()

    return redirect(url_for("main.student_chat", chat_id=chat_id))

@main.route("/delete-chat/<int:chat_id>")
def delete_chat(chat_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()

    chat = connection.execute(
        """
        SELECT chat_id
        FROM chats
        WHERE chat_id = ? AND user_id = ?
        """,
        (chat_id, session["user_id"])
    ).fetchone()

    if chat:

        connection.execute(
            """
            DELETE FROM messages
            WHERE chat_id = ?
            """,
            (chat_id,)
        )

        connection.execute(
            """
            DELETE FROM chats
            WHERE chat_id = ? AND user_id = ?
            """,
            (chat_id, session["user_id"])
        )

        connection.commit()

    connection.close()

    return redirect(url_for("main.student_chat"))

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