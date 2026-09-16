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
from projects import (
    create_project_with_tasks,
    get_project,
    get_task_dates,
    list_projects_with_tasks,
    update_task_dates,
    update_project_with_tasks,
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


@app.route("/admin/projects/<int:project_id>/edit")
def edit_project_page(project_id):
    if not session.get("is_admin"):
        return "Admin access required", 403
    project = get_project(project_id)
    if project is None:
        return "Project not found", 404
    return render_template("edit_project.html", project=project)


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


@app.post("/api/admin/projects")
def create_admin_project():
    access_error = admin_required()
    if access_error:
        return access_error

    project_data = request.get_json(silent=True) or {}
    name = str(project_data.get("name", "")).strip()
    start_date = str(project_data.get("start_date", "")).strip()
    tasks = project_data.get("tasks", [])
    if not name or not start_date or not isinstance(tasks, list) or not tasks:
        return jsonify(message="Project name, start date, and tasks are required"), 400

    normalized_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            return jsonify(message="Each task must be an object"), 400
        title = str(task.get("title", "")).strip()
        task_start = str(task.get("start_date", "")).strip()
        task_end = str(task.get("end_date", "")).strip()
        actual_start = str(task.get("actual_start_date", "")).strip()
        actual_end = str(task.get("actual_end_date", "")).strip()
        if not title or not task_start or not task_end or not actual_start or not actual_end:
            return jsonify(message="Each task needs budgeted and actual dates"), 400
        if actual_start > actual_end:
            return jsonify(message="Actual start date cannot be after end date"), 400
        try:
            labor_hours = float(task.get("labor_hours"))
            material_cost = float(task.get("material_cost"))
            subcontractor_cost = float(task.get("subcontractor_cost"))
        except (TypeError, ValueError):
            return jsonify(message="Task budgets must be numbers"), 400
        if min(labor_hours, material_cost, subcontractor_cost) < 0:
            return jsonify(message="Task budgets cannot be negative"), 400
        normalized_tasks.append(
            {
                "title": title,
                "start_date": task_start,
                "end_date": task_end,
                "labor_hours": labor_hours,
                "material_cost": material_cost,
                "subcontractor_cost": subcontractor_cost,
                "actual_start_date": actual_start,
                "actual_end_date": actual_end,
            }
        )

    project_id = create_project_with_tasks(name, start_date, normalized_tasks)
    return jsonify(message="Project created", project_id=project_id), 201


@app.put("/api/admin/projects/<int:project_id>")
def update_admin_project(project_id):
    access_error = admin_required()
    if access_error:
        return access_error

    project_data = request.get_json(silent=True) or {}
    name = str(project_data.get("name", "")).strip()
    start_date = str(project_data.get("start_date", "")).strip()
    end_date = str(project_data.get("end_date", "")).strip()
    tasks = project_data.get("tasks", [])
    if not name or not start_date or not end_date:
        return jsonify(message="Project name and dates are required"), 400
    if not isinstance(tasks, list):
        return jsonify(message="Tasks must be a list"), 400

    normalized_tasks = []
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            return jsonify(message="Each task needs an id"), 400
        actual_start = str(task.get("actual_start_date", "")).strip()
        actual_end = str(task.get("actual_end_date", "")).strip()
        if bool(actual_start) != bool(actual_end):
            return jsonify(message="Actual start and end dates must be entered together"), 400
        if actual_start and actual_start > actual_end:
            return jsonify(message="Actual start date cannot be after actual end date"), 400
        normalized_tasks.append(
            {
                "id": task["id"],
                "actual_start_date": actual_start,
                "actual_end_date": actual_end,
            }
        )

    if not update_project_with_tasks(
        project_id, name, start_date, end_date, normalized_tasks
    ):
        return jsonify(message="Project not found"), 404
    return jsonify(message="Project updated", project=get_project(project_id))


@app.put("/api/admin/tasks/<int:task_id>")
def update_admin_task(task_id):
    task_data = request.get_json(silent=True) or {}
    task_updates = task_data.get("tasks") or [dict(task_data, id=task_id)]
    normalized_updates = []
    for task in task_updates:
        dates = {
            "id": task.get("id"),
            "start_date": str(task.get("start_date", "")).strip(),
            "end_date": str(task.get("end_date", "")).strip(),
            "actual_start_date": str(task.get("actual_start_date", "")).strip(),
            "actual_end_date": str(task.get("actual_end_date", "")).strip(),
            "completed": bool(task.get("completed", False)),
        }
        if not dates["id"] or not dates["start_date"] or not dates["end_date"]:
            return jsonify(message="Budgeted task dates are required"), 400
        if dates["start_date"] > dates["end_date"]:
            return jsonify(message="Budgeted start date cannot be after end date"), 400
        if bool(dates["actual_start_date"]) != bool(dates["actual_end_date"]):
            return jsonify(message="Actual start and end dates must be entered together"), 400
        if dates["actual_start_date"] and dates["actual_start_date"] > dates["actual_end_date"]:
            return jsonify(message="Actual start date cannot be after actual end date"), 400
        normalized_updates.append(dates)

    if task_id not in [task["id"] for task in normalized_updates]:
        return jsonify(message="Task update does not match route"), 400
    if not session.get("is_admin"):
        existing_dates = get_task_dates([task["id"] for task in normalized_updates])
        if any(
            task["id"] not in existing_dates
            or task["start_date"] != existing_dates[task["id"]]["start_date"]
            or task["end_date"] != existing_dates[task["id"]]["end_date"]
            for task in normalized_updates
        ):
            return jsonify(message="Only administrators can move budgeted timelines"), 403
    try:
        project_id = update_task_dates(normalized_updates)
    except ValueError as error:
        return jsonify(message=str(error)), 409
    if project_id is None:
        return jsonify(message="Task not found"), 404
    return jsonify(message="Task dates updated", project_id=project_id)


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