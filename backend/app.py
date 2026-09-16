import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import (
    authenticate_user,
    create_regular_user,
    delete_regular_user,
    list_regular_users,
    update_regular_user,
)

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


@app.route("/admin")
def admin_page():
    if not session.get("is_admin"):
        return "Admin access required", 403
    return render_template("admin.html")


@app.route("/api/test")
def api_test():
    return jsonify(message="API is working")


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


def admin_required():
    if not session.get("is_admin"):
        return jsonify(message="Admin access required"), 403
    return None


@app.get("/api/admin/users")
def admin_users():
    access_error = admin_required()
    if access_error:
        return access_error
    return jsonify(users=list_regular_users())


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