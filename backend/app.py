import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import (
    authenticate_user,
    create_regular_user,
    delete_regular_user,
    get_user_profile,
    list_users,
    update_user_profile,
    update_regular_user,
)
from projects import list_projects_with_tasks

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)
app.config["SECRET_KEY"] = "development-only-change-me"


@app.route("/")
def index():
    if not session.get("username"):
        return redirect(url_for("login_page"))
    return render_template("home.html")


@app.route("/login")
def login_page():
    if session.get("username"):
        return redirect(url_for("index"))
    return render_template("index.html")


@app.route("/register")
def register_page():
    if session.get("username"):
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/admin")
def admin_page():
    if not session.get("is_admin"):
        return "Admin access required", 403
    return render_template("admin.html")


@app.route("/profile")
def profile_page():
    username = session.get("username")
    if username is None:
        return redirect(url_for("login_page"))

    requested_username = request.args.get("username", username)
    if requested_username != username and not session.get("is_admin"):
        return "Admin access required", 403
    return render_template("profile.html", profile_username=requested_username)


@app.route("/api/test")
def api_test():
    return jsonify(message="API is working")


@app.get("/api/projects")
def projects():
    if not session.get("username"):
        return jsonify(message="Authentication required"), 401
    return jsonify(projects=list_projects_with_tasks())


@app.post("/api/login")
def login():
    credentials = request.get_json(silent=True) or {}
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "")
    user = authenticate_user(username, password)

    if user is None:
        return jsonify(message="Invalid username or password"), 401

    session["username"] = user["username"]
    session["is_admin"] = user["is_admin"]
    return jsonify(
        message="Login successful",
        username=user["username"],
        is_admin=user["is_admin"],
    )


@app.post("/api/register")
def register():
    user_data = request.get_json(silent=True) or {}
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")
    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    try:
        create_regular_user(username, password)
    except sqlite3.IntegrityError:
        return jsonify(message="Username already exists"), 409
    return jsonify(message="Registration successful"), 201


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(message="Logged out")


@app.get("/api/me")
def current_user():
    username = session.get("username")
    if username is None:
        return jsonify(authenticated=False), 401
    return jsonify(
        authenticated=True,
        username=username,
        is_admin=session.get("is_admin", False),
    )


@app.get("/api/profile/<username>")
def profile(username):
    current_username = session.get("username")
    if current_username is None:
        return jsonify(message="Authentication required"), 401
    if username != current_username and not session.get("is_admin"):
        return jsonify(message="Admin access required"), 403

    user_profile = get_user_profile(username)
    if user_profile is None:
        return jsonify(message="User not found"), 404
    return jsonify(profile=user_profile)


@app.put("/api/profile/<username>")
def update_profile(username):
    current_username = session.get("username")
    if current_username is None:
        return jsonify(message="Authentication required"), 401
    if username != current_username and not session.get("is_admin"):
        return jsonify(message="Admin access required"), 403

    user_data = request.get_json(silent=True) or {}
    required_fields = ("first_name", "last_name", "email", "start_date", "title")
    if any(not str(user_data.get(field, "")).strip() for field in required_fields):
        return jsonify(message="All profile fields are required"), 400

    try:
        pay_rate = float(user_data.get("pay_rate"))
    except (TypeError, ValueError):
        return jsonify(message="Pay rate must be a number"), 400
    if pay_rate < 0:
        return jsonify(message="Pay rate cannot be negative"), 400

    profile_data = {
        field: str(user_data[field]).strip() for field in required_fields
    }
    profile_data["pay_rate"] = pay_rate
    if not update_user_profile(username, profile_data):
        return jsonify(message="User not found"), 404
    return jsonify(message="Profile updated", profile=get_user_profile(username))


def admin_required():
    if not session.get("is_admin"):
        return jsonify(message="Admin access required"), 403
    return None


@app.get("/api/admin/users")
def admin_users():
    access_error = admin_required()
    if access_error:
        return access_error
    return jsonify(users=list_users())


@app.post("/api/admin/users")
def create_admin_user():
    access_error = admin_required()
    if access_error:
        return access_error

    user_data = request.get_json(silent=True) or {}
    username = user_data.get("username", "").strip()
    password = user_data.get("password", "")
    if not username or not password:
        return jsonify(message="Username and password are required"), 400

    try:
        create_regular_user(username, password)
    except sqlite3.IntegrityError:
        return jsonify(message="Username already exists"), 409
    return jsonify(message="User created", username=username), 201


@app.put("/api/admin/users/<username>")
def update_admin_user(username):
    access_error = admin_required()
    if access_error:
        return access_error

    user_data = request.get_json(silent=True) or {}
    new_username = user_data.get("username", "").strip()
    password = user_data.get("password", "")
    if not new_username:
        return jsonify(message="Username is required"), 400

    try:
        updated = update_regular_user(username, new_username, password or None)
    except sqlite3.IntegrityError:
        return jsonify(message="Username already exists"), 409
    if not updated:
        return jsonify(message="Regular user not found"), 404
    return jsonify(message="User updated", username=new_username)


@app.delete("/api/admin/users/<username>")
def delete_admin_user(username):
    access_error = admin_required()
    if access_error:
        return access_error
    if not delete_regular_user(username):
        return jsonify(message="Regular user not found"), 404
    return jsonify(message="User deleted")


if __name__ == "__main__":
    app.run(debug=True)