
import os
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from getpass import getpass

import jwt
from pwdlib import PasswordHash


DB_PATH = Path("data/users.db")
password_hash = PasswordHash.recommended()

ROLES = ["admin", "manager", "employee"]
CLEARANCE_LEVELS = ["public", "internal", "confidential"]


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                department TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)

        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(users)"
            ).fetchall()
        }

        if "clearance_level" not in columns:
            conn.execute("""
                ALTER TABLE users
                ADD COLUMN clearance_level TEXT NOT NULL DEFAULT 'public'
            """)


def create_user(
    username,
    password,
    role,
    tenant_id,
    department=None,
    clearance_level="public"
):
    if role not in ROLES:
        raise ValueError("Invalid role")

    if clearance_level not in CLEARANCE_LEVELS:
        raise ValueError("Invalid clearance level")

    if not username.strip() or len(password) < 8:
        raise ValueError(
            "Username is required and password must be at least 8 characters"
        )

    if not tenant_id.strip():
        raise ValueError("Tenant ID is required")

    user_id = str(uuid.uuid4())
    hashed_password = password_hash.hash(password)

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users
            (
                user_id, username, password_hash, role,
                tenant_id, department, clearance_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            username.strip(),
            hashed_password,
            role,
            tenant_id.strip(),
            department,
            clearance_level
        ))

    return user_id


def get_user_by_username(username):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT * FROM users
            WHERE user_id = ? AND is_active = 1
            """,
            (user_id,)
        ).fetchone()

    return dict(row) if row else None


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id):
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is missing")

    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
    }

    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token):
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is missing")

    return jwt.decode(
        token,
        secret,
        algorithms=["HS256"]
    )


init_db()


if __name__ == "__main__":
    print("Create an application user")

    username = input("Username: ").strip()
    password = getpass("Password (minimum 8 characters): ")
    role = input("Role (admin/manager/employee): ").strip().lower()
    tenant_id = input("Tenant ID: ").strip()
    department = input("Department (or leave blank): ").strip() or None
    clearance = input(
        "Clearance (public/internal/confidential): "
    ).strip().lower()

    try:
        user_id = create_user(
            username,
            password,
            role,
            tenant_id,
            department,
            clearance
        )

        print("User created successfully!")
        print("User ID:", user_id)
        print("Role:", role)
        print("Tenant:", tenant_id)
        print("Clearance:", clearance)

    except (ValueError, sqlite3.IntegrityError) as error:
        print("Could not create user:", error)
