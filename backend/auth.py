import sqlite3
from pathlib import Path

import bcrypt


DATABASE_PATH = Path(__file__).with_name("users.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def authenticate_user(username, password):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT username, password_hash, is_admin FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if user is None or not bcrypt.checkpw(
        password.encode("utf-8"), user["password_hash"]
    ):
        return None

    return {"username": user["username"], "is_admin": bool(user["is_admin"])}


def list_regular_users():
    with get_connection() as connection:
        users = connection.execute(
            "SELECT username FROM users WHERE is_admin = 0 ORDER BY username"
        ).fetchall()
    return [{"username": user["username"]} for user in users]


def create_regular_user(username, password):
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 0)",
            (username, password_hash),
        )


def update_regular_user(username, new_username, password=None):
    with get_connection() as connection:
        if password:
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            connection.execute(
                "UPDATE users SET username = ?, password_hash = ? "
                "WHERE username = ? AND is_admin = 0",
                (new_username, password_hash, username),
            )
        else:
            connection.execute(
                "UPDATE users SET username = ? WHERE username = ? AND is_admin = 0",
                (new_username, username),
            )
        return connection.total_changes > 0


def delete_regular_user(username):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM users WHERE username = ? AND is_admin = 0", (username,)
        )
        return connection.total_changes > 0