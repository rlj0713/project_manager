import bcrypt

from auth import get_connection


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
                is_admin INTEGER NOT NULL DEFAULT 0
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
    print("Seeded users: alice (admin), bob (non-admin), carol (non-admin)")