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


def delete_job(job_id: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def list_all_job_ids() -> set[str]:
    conn = _get_conn()
    rows = conn.execute("SELECT id FROM jobs").fetchall()
    conn.close()
    return {r["id"] for r in rows}


def sync_jobs(folders: dict[str, dict]) -> dict:
    """以文件夹为准同步数据库。

    folders: {folder_name: {type, status, created_at, ...}}
    返回 {created: int, deleted: int}
    """
    db_ids = list_all_job_ids()
    folder_names = set(folders.keys())

    created = 0
    deleted = 0

    # 文件夹有但 DB 没有的 → 创建
    for name in folder_names - db_ids:
        info = folders[name]
        conn = _get_conn()
        conn.execute(
            "INSERT INTO jobs (id, type, status, params, created_at) VALUES (?,?,?,?,?)",
            (name, info.get("type", "unknown"), info.get("status", "success"),
             json.dumps(info.get("params", {}), ensure_ascii=False),
             info.get("created_at", time.time())),
        )
        conn.commit()
        conn.close()
        created += 1

    # DB 有但文件夹没有的 → 删除
    for name in db_ids - folder_names:
        delete_job(name)
        deleted += 1

    return {"created": created, "deleted": deleted}
