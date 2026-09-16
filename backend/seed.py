import bcrypt

from auth import get_connection
from projects import seed_sample_projects


SEED_USERS = {
    "alice": {"password": "alice123", "is_admin": True},
    "bob": {"password": "bob123", "is_admin": False},
    "carol": {"password": "carol123", "is_admin": False},
}


def seed_users():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                first_name TEXT NOT NULL DEFAULT '',
                last_name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                start_date TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                pay_rate REAL NOT NULL DEFAULT 0
            )
            """
        )

        columns = {
            column[1]
            for column in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "is_admin" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
            )
        profile_columns = {
            "first_name": "TEXT NOT NULL DEFAULT ''",
            "last_name": "TEXT NOT NULL DEFAULT ''",
            "email": "TEXT NOT NULL DEFAULT ''",
            "start_date": "TEXT NOT NULL DEFAULT ''",
            "title": "TEXT NOT NULL DEFAULT ''",
            "pay_rate": "REAL NOT NULL DEFAULT 0",
        }
        for column, definition in profile_columns.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE users ADD COLUMN {column} {definition}"
                )

        for username, user_data in SEED_USERS.items():
            password_hash = bcrypt.hashpw(
                user_data["password"].encode("utf-8"), bcrypt.gensalt()
            )
            connection.execute(
                """
                INSERT INTO users (username, password_hash, is_admin)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET is_admin = excluded.is_admin
                """,
                (username, password_hash, user_data["is_admin"]),
            )


if __name__ == "__main__":
    seed_users()
    seed_sample_projects()
    print("Seeded users: alice (admin), bob (non-admin), carol (non-admin)")