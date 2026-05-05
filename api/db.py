"""SQLite 任务存储。"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from enum import Enum
from pathlib import Path

DB_PATH = Path("data/jobs.db")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id         TEXT PRIMARY KEY,
        type       TEXT NOT NULL,
        status     TEXT NOT NULL DEFAULT 'pending',
        params     TEXT NOT NULL DEFAULT '{}',
        result     TEXT,
        error      TEXT,
        created_at REAL NOT NULL,
        started_at REAL,
        finished_at REAL
    )""")
    conn.commit()
    return conn


def create_job(job_type: str, params: dict) -> str:
    job_id = f"{job_type}-{uuid.uuid4().hex[:8]}"
    conn = _get_conn()
    conn.execute(
        "INSERT INTO jobs (id, type, params, status, created_at) VALUES (?,?,?,?,?)",
        (job_id, job_type, json.dumps(params, ensure_ascii=False), JobStatus.PENDING.value, time.time()),
    )
    conn.commit()
    conn.close()
    return job_id


def update_job(job_id: str, **kwargs) -> None:
    allowed = {"status", "result", "error", "started_at", "finished_at"}
    sets, vals = [], []
    for k, v in kwargs.items():
        if k not in allowed:
            continue
        sets.append(f"{k} = ?")
        if k in ("result",) and isinstance(v, dict):
            vals.append(json.dumps(v, ensure_ascii=False))
        else:
            vals.append(v)
    if not sets:
        return
    vals.append(job_id)
    conn = _get_conn()
    conn.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def get_job(job_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def list_jobs(status: str | None = None, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for key in ("params", "result"):
        if d.get(key) and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
