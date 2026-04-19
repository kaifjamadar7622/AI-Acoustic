import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "acoustic_artistry.db"
GENERATED_DIR = DATA_DIR / "generated"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transcript TEXT NOT NULL,
                prompt TEXT NOT NULL,
                negative_prompt TEXT NOT NULL,
                style_name TEXT NOT NULL,
                status TEXT NOT NULL,
                image_paths_json TEXT NOT NULL,
                audio_path TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


def _hash_password(password: str, salt_hex: str | None = None) -> str:
    salt_hex = salt_hex or secrets.token_hex(16)
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()
    return f"{salt_hex}${digest}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    return _hash_password(password, salt_hex) == password_hash


def register_user(username: str, password: str, display_name: str = "") -> tuple[bool, str]:
    init_storage()
    username = _normalize_username(username)
    display_name = (display_name or username).strip() or username

    if not username:
        return False, "Username is required."
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."

    with _connect() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return False, "That username already exists."

        conn.execute(
            "INSERT INTO users (username, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, display_name, _hash_password(password), _utc_now()),
        )
        conn.commit()
    return True, f"Account created for {display_name}. You can sign in now."


def authenticate_user(username: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    init_storage()
    username = _normalize_username(username)

    if not username or not password:
        return False, "Enter username and password.", None

    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, display_name, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return False, "Invalid username or password.", None
        if not _verify_password(password, row["password_hash"]):
            return False, "Invalid username or password.", None

    return True, f"Welcome back, {row['display_name']}", {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "created_at": row["created_at"],
    }


def get_user(username: str) -> dict[str, Any] | None:
    init_storage()
    username = _normalize_username(username)
    if not username:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, display_name, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
    return dict(row)


def save_generation_assets(username: str, images: list[Any], timestamp: str | None = None) -> list[str]:
    init_storage()
    user_dir = GENERATED_DIR / _normalize_username(username or "anonymous")
    user_dir.mkdir(parents=True, exist_ok=True)
    timestamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    saved_paths: list[str] = []
    for index, image in enumerate(images, start=1):
        image_path = user_dir / f"{timestamp}_{index}.png"
        image.save(image_path)
        saved_paths.append(str(image_path))
    return saved_paths


def save_generation_history(
    username: str,
    transcript: str,
    prompt: str,
    negative_prompt: str,
    style_name: str,
    image_paths: list[str],
    audio_path: str | None,
    status: str,
) -> None:
    init_storage()
    user = get_user(username)
    if user is None:
        return

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO generations
                (user_id, transcript, prompt, negative_prompt, style_name, status, image_paths_json, audio_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                transcript,
                prompt,
                negative_prompt,
                style_name,
                status,
                json.dumps(image_paths),
                audio_path,
                _utc_now(),
            ),
        )
        conn.commit()


def get_user_history(username: str, limit: int = 10) -> list[dict[str, Any]]:
    init_storage()
    user = get_user(username)
    if user is None:
        return []

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT transcript, prompt, negative_prompt, style_name, status, image_paths_json, audio_path, created_at
            FROM generations
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user["id"], limit),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        history.append(
            {
                "created_at": row["created_at"],
                "style_name": row["style_name"],
                "transcript": row["transcript"],
                "prompt": row["prompt"],
                "negative_prompt": row["negative_prompt"],
                "status": row["status"],
                "audio_path": row["audio_path"],
                "image_paths": json.loads(row["image_paths_json"]),
            }
        )
    return history


def history_table_rows(username: str, limit: int = 10) -> list[list[str]]:
    history = get_user_history(username, limit=limit)
    rows: list[list[str]] = []
    for item in history:
        transcript = item["transcript"]
        if len(transcript) > 60:
            transcript = transcript[:57] + "..."
        rows.append([
            item["created_at"],
            item["style_name"],
            transcript,
            item["status"],
        ])
    return rows


def history_gallery_items(username: str, limit: int = 5) -> list[str]:
    history = get_user_history(username, limit=limit)
    images: list[str] = []
    for item in history:
        images.extend(item["image_paths"])
    return images
