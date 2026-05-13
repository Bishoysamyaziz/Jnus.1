"""OneAgent OS — Database Layer (Lightweight SQLite)
Usage tracking, user data, task logging.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Optional


DB_PATH = os.getenv("DATABASE_PATH", "/tmp/oneagent.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_limit INTEGER DEFAULT 5,
                usage_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS usage_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                prompt TEXT,
                mode TEXT,
                result_summary TEXT,
                duration REAL,
                status TEXT DEFAULT 'pending',
                error TEXT,
                cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT,
                prompt TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'build',
                status TEXT DEFAULT 'running',
                result_url TEXT,
                files TEXT,
                logs TEXT,
                duration REAL,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_usage_date ON usage_logs(created_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
        """)
        conn.commit()
    finally:
        conn.close()


class UsageTracker:
    """Track and enforce usage limits per user."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_user(self, user_id: str) -> Optional[dict]:
        """Get user by ID."""
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_user(self, user_id: str, email: str) -> dict:
        """Create a new user."""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
                (user_id, email),
            )
            conn.commit()
            return self.get_user(user_id) or {"id": user_id, "email": email}
        finally:
            conn.close()

    def get_daily_usage(self, user_id: str) -> int:
        """Get number of tasks run today."""
        conn = self._get_conn()
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            row = conn.execute(
                """SELECT COUNT(*) as count FROM usage_logs 
                   WHERE user_id = ? AND date(created_at) = ? AND action = 'run_task'""",
                (user_id, today),
            ).fetchone()
            return row["count"] if row else 0
        finally:
            conn.close()

    def check_limit(self, user_id: str) -> tuple[bool, int]:
        """Check if user has exceeded their daily limit.
        Returns (allowed, remaining)
        """
        user = self.get_user(user_id)
        if not user:
            return True, 5  # Default limit for new users

        limit = user.get("usage_limit", 5)
        used = self.get_daily_usage(user_id)
        remaining = max(0, limit - used)

        return remaining > 0, remaining

    def log_usage(
        self,
        user_id: str,
        action: str,
        prompt: Optional[str] = None,
        mode: Optional[str] = None,
        result_summary: Optional[str] = None,
        duration: Optional[float] = None,
        status: str = "completed",
        error: Optional[str] = None,
        cost: float = 0,
    ) -> str:
        """Log a usage event."""
        conn = self._get_conn()
        log_id = str(uuid.uuid4())
        try:
            conn.execute(
                """INSERT INTO usage_logs 
                   (id, user_id, action, prompt, mode, result_summary, duration, status, error, cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (log_id, user_id, action, prompt, mode, result_summary, duration, status, error, cost),
            )
            conn.commit()
            return log_id
        finally:
            conn.close()

    def save_task(
        self,
        user_id: str,
        prompt: str,
        mode: str = "build",
        status: str = "running",
        result_url: Optional[str] = None,
        files: Optional[list] = None,
        logs: Optional[list] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None,
    ) -> str:
        """Save a task execution record."""
        conn = self._get_conn()
        task_id = str(uuid.uuid4())
        try:
            conn.execute(
                """INSERT INTO tasks 
                   (id, user_id, prompt, mode, status, result_url, files, logs, duration, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    user_id,
                    prompt,
                    mode,
                    status,
                    result_url,
                    json.dumps(files or []),
                    json.dumps(logs or []),
                    duration,
                    error,
                ),
            )
            conn.commit()
            return task_id
        finally:
            conn.close()

    def get_tasks(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get recent tasks for a user."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            result = []
            for row in rows:
                d = dict(row)
                if d.get("files") and isinstance(d["files"], str):
                    try:
                        d["files"] = json.loads(d["files"])
                    except json.JSONDecodeError:
                        pass
                if d.get("logs") and isinstance(d["logs"], str):
                    try:
                        d["logs"] = json.loads(d["logs"])
                    except json.JSONDecodeError:
                        pass
                result.append(d)
            return result
        finally:
            conn.close()

    def get_usage_stats(self, user_id: str) -> dict:
        """Get usage statistics for a user."""
        conn = self._get_conn()
        try:
            # Daily count
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_row = conn.execute(
                "SELECT COUNT(*) as count FROM usage_logs WHERE user_id = ? AND date(created_at) = ?",
                (user_id, today),
            ).fetchone()

            # Total count
            total_row = conn.execute(
                "SELECT COUNT(*) as count FROM usage_logs WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            # Last task
            last_row = conn.execute(
                "SELECT created_at, status FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()

            user = self.get_user(user_id)
            limit = user.get("usage_limit", 5) if user else 5
            daily = daily_row["count"] if daily_row else 0

            return {
                "daily_used": daily,
                "daily_limit": limit,
                "daily_remaining": max(0, limit - daily),
                "total_tasks": total_row["count"] if total_row else 0,
                "last_task": dict(last_row) if last_row else None,
            }
        finally:
            conn.close()
