from auth import get_connection


def initialize_project_tables():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                labor_hours REAL NOT NULL DEFAULT 0,
                material_cost REAL NOT NULL DEFAULT 0,
                subcontractor_cost REAL NOT NULL DEFAULT 0,
                actual_start_date TEXT NOT NULL DEFAULT '',
                actual_end_date TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
            """
        )
        columns = {
            column[1]
            for column in connection.execute("PRAGMA table_info(tasks)").fetchall()
        }
        for column, definition in {
            "labor_hours": "REAL NOT NULL DEFAULT 0",
            "material_cost": "REAL NOT NULL DEFAULT 0",
            "subcontractor_cost": "REAL NOT NULL DEFAULT 0",
            "actual_start_date": "TEXT NOT NULL DEFAULT ''",
            "actual_end_date": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE tasks ADD COLUMN {column} {definition}"
                )


def seed_sample_projects():
    initialize_project_tables()
    with get_connection() as connection:
        project_count = connection.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]
        if project_count:
            return

        projects = [
            ("Northwind rollout", "2026-09-01", "2026-10-15"),
            ("Field operations portal", "2026-09-10", "2026-11-07"),
            ("Annual planning", "2026-10-01", "2026-11-20"),
        ]
        connection.executemany(
            "INSERT INTO projects (name, start_date, end_date) VALUES (?, ?, ?)",
            projects,
        )
        project_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM projects").fetchall()
        }
        tasks = [
            (project_ids["Northwind rollout"], "Discovery", "2026-09-01", "2026-09-08", 1),
            (project_ids["Northwind rollout"], "Implementation", "2026-09-09", "2026-09-30", 1),
            (project_ids["Northwind rollout"], "Launch", "2026-10-01", "2026-10-15", 0),
            (project_ids["Field operations portal"], "User research", "2026-09-10", "2026-09-22", 1),
            (project_ids["Field operations portal"], "Prototype", "2026-09-23", "2026-10-12", 0),
            (project_ids["Field operations portal"], "Pilot", "2026-10-13", "2026-11-07", 0),
            (project_ids["Annual planning"], "Collect inputs", "2026-10-01", "2026-10-16", 0),
            (project_ids["Annual planning"], "Review", "2026-10-17", "2026-11-05", 0),
            (project_ids["Annual planning"], "Publish plan", "2026-11-06", "2026-11-20", 0),
        ]
        connection.executemany(
            """
            INSERT INTO tasks
                (project_id, title, start_date, end_date, completed)
            VALUES (?, ?, ?, ?, ?)
            """,
            tasks,
        )


def list_projects_with_tasks():
    initialize_project_tables()
    with get_connection() as connection:
        projects = connection.execute(
            "SELECT id, name, start_date, end_date FROM projects ORDER BY start_date, id"
        ).fetchall()
        tasks = connection.execute(
            """
            SELECT id, project_id, title, start_date, end_date, completed,
                labor_hours, material_cost, subcontractor_cost,
                actual_start_date, actual_end_date
            FROM tasks
            ORDER BY start_date, id
            """
        ).fetchall()

    tasks_by_project = {}
    for task in tasks:
        tasks_by_project.setdefault(task["project_id"], []).append(
            {
                "id": task["id"],
                "title": task["title"],
                "start_date": task["start_date"],
                "end_date": task["end_date"],
                "completed": bool(task["completed"]),
                "labor_hours": task["labor_hours"],
                "material_cost": task["material_cost"],
                "subcontractor_cost": task["subcontractor_cost"],
                "actual_start_date": task["actual_start_date"],
                "actual_end_date": task["actual_end_date"],
            }
        )

    return [
        {
            "id": project["id"],
            "name": project["name"],
            "start_date": project["start_date"],
            "end_date": project["end_date"],
            "tasks": tasks_by_project.get(project["id"], []),
        }
        for project in projects
    ]


def get_project(project_id):
    initialize_project_tables()
    with get_connection() as connection:
        project = connection.execute(
            "SELECT id, name, start_date, end_date FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if project is None:
            return None
        tasks = connection.execute(
            """
            SELECT id, title, start_date, end_date, completed,
                labor_hours, material_cost, subcontractor_cost,
                actual_start_date, actual_end_date
            FROM tasks
            WHERE project_id = ?
            ORDER BY start_date, id
            """,
            (project_id,),
        ).fetchall()
    result = dict(project)
    result["tasks"] = [dict(task) for task in tasks]
    return result


def update_project_with_tasks(project_id, name, start_date, end_date, tasks):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE projects
            SET name = ?, start_date = ?, end_date = ?
            WHERE id = ?
            """,
            (name, start_date, end_date, project_id),
        )
        if connection.total_changes == 0:
            return False
        for task in tasks:
            connection.execute(
                """
                UPDATE tasks
                SET actual_start_date = ?, actual_end_date = ?
                WHERE id = ? AND project_id = ?
                """,
                (
                    task["actual_start_date"],
                    task["actual_end_date"],
                    task["id"],
                    project_id,
                ),
            )
    return True


def update_task_dates(task_updates):
    initialize_project_tables()
    with get_connection() as connection:
        task_ids = [task["id"] for task in task_updates]
        placeholders = ",".join("?" for _ in task_ids)
        task = connection.execute(
            f"SELECT project_id FROM tasks WHERE id IN ({placeholders}) LIMIT 1",
            task_ids,
        ).fetchone()
        if task is None:
            return None

        for dates in task_updates:
            connection.execute(
                """
                UPDATE tasks
                SET start_date = ?, end_date = ?,
                    actual_start_date = ?, actual_end_date = ?
                WHERE id = ? AND project_id = ?
                """,
                (
                    dates["start_date"],
                    dates["end_date"],
                    dates["actual_start_date"],
                    dates["actual_end_date"],
                    dates["id"],
                    task["project_id"],
                ),
            )
        budget_tasks = connection.execute(
            "SELECT start_date, end_date FROM tasks WHERE project_id = ? "
            "ORDER BY start_date, id",
            (task["project_id"],),
        ).fetchall()
        if any(
            current["end_date"] >= following["start_date"]
            for current, following in zip(budget_tasks, budget_tasks[1:])
        ):
            raise ValueError("Budgeted tasks cannot overlap")

        actual_tasks = connection.execute(
            """
            SELECT actual_start_date, actual_end_date
            FROM tasks
            WHERE project_id = ? AND actual_start_date != '' AND actual_end_date != ''
            ORDER BY actual_start_date, id
            """,
            (task["project_id"],),
        ).fetchall()
        if any(
            current["actual_end_date"] >= following["actual_start_date"]
            for current, following in zip(actual_tasks, actual_tasks[1:])
        ):
            raise ValueError("Actual task dates cannot overlap")

        budget_range = connection.execute(
            """
            SELECT MIN(start_date), MAX(end_date)
            FROM tasks WHERE project_id = ?
            """,
            (task["project_id"],),
        ).fetchone()
        connection.execute(
            "UPDATE projects SET start_date = ?, end_date = ? WHERE id = ?",
            (budget_range[0], budget_range[1], task["project_id"]),
        )
    return task["project_id"]


def create_project_with_tasks(name, start_date, tasks):
    initialize_project_tables()
    project_end_date = max(task["end_date"] for task in tasks)
    with get_connection() as connection:
        project = connection.execute(
            """
            INSERT INTO projects (name, start_date, end_date)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (name, start_date, project_end_date),
        ).fetchone()
        connection.executemany(
            """
            INSERT INTO tasks
                (project_id, title, start_date, end_date, completed,
                 labor_hours, material_cost, subcontractor_cost)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            [
                (
                    project["id"],
                    task["title"],
                    task["start_date"],
                    task["end_date"],
                    task["labor_hours"],
                    task["material_cost"],
                    task["subcontractor_cost"],
                )
                for task in tasks
            ],
        )
    return project["id"]