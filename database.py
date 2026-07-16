"""数据库初始化与基础操作"""
import sqlite3
import json
from typing import Optional, List
from datetime import date
from config import DB_PATH
from models import Project, ProgressRecord, Note, ModuleInfo


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            type            TEXT NOT NULL DEFAULT 'book',
            source          TEXT DEFAULT 'other',
            url             TEXT DEFAULT '',
            progress_type   TEXT NOT NULL DEFAULT 'linear',
            total_units     INTEGER,
            unit_label      TEXT DEFAULT '页',
            modules_json    TEXT DEFAULT '[]',
            expected_end_date TEXT,
            priority        TEXT DEFAULT 'medium',
            tags            TEXT DEFAULT '',
            status          TEXT DEFAULT 'backlog',
            total_progress  REAL DEFAULT 0,
            last_active_date TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS progress_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER NOT NULL,
            record_date     TEXT NOT NULL,
            start_value     INTEGER,
            end_value       INTEGER,
            module_index    INTEGER,
            module_name     TEXT,
            part_start      INTEGER,
            part_end        INTEGER,
            total_parts     INTEGER,
            progress_note   TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER NOT NULL,
            title           TEXT NOT NULL,
            content         TEXT DEFAULT '',
            chapter_tag     TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_progress_project 
            ON progress_records(project_id, record_date);
        CREATE INDEX IF NOT EXISTS idx_notes_project 
            ON notes(project_id);
    """)

    conn.commit()
    conn.close()


# ─── 转换辅助函数 ───

def row_to_project(row: sqlite3.Row) -> Project:
    """将数据库行转换为Project对象"""
    modules_json = row["modules_json"] or "[]"
    modules = []
    for m in json.loads(modules_json):
        modules.append(ModuleInfo(name=m["name"], total_parts=m["total_parts"]))

    return Project(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        source=row["source"],
        url=row["url"] or "",
        progress_type=row["progress_type"],
        total_units=row["total_units"],
        unit_label=row["unit_label"] or "页",
        modules=modules,
        expected_end_date=_parse_date(row["expected_end_date"]),
        priority=row["priority"],
        tags=[t.strip() for t in (row["tags"] or "").split(",") if t.strip()],
        status=row["status"],
        total_progress=row["total_progress"] or 0,
        last_active_date=_parse_date(row["last_active_date"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_progress(row: sqlite3.Row) -> ProgressRecord:
    """将数据库行转换为ProgressRecord对象"""
    return ProgressRecord(
        id=row["id"],
        project_id=row["project_id"],
        record_date=_parse_date(row["record_date"]) or date.today(),
        start_value=row["start_value"],
        end_value=row["end_value"],
        module_index=row["module_index"],
        module_name=row["module_name"],
        part_start=row["part_start"],
        part_end=row["part_end"],
        total_parts=row["total_parts"],
        progress_note=row["progress_note"] or "",
        created_at=row["created_at"],
    )


def row_to_note(row: sqlite3.Row) -> Note:
    """将数据库行转换为Note对象"""
    return Note(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"] or "",
        chapter_tag=row["chapter_tag"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """安全解析日期字符串"""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None
    

def get_project_count_by_status(status: str) -> int:
    """获取指定状态的项目数量"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM projects WHERE status=?", (status,))
    result = cursor.fetchone()["cnt"]
    conn.close()
    return result


def get_all_tags() -> List[str]:
    """获取所有已使用的标签（用于自动补全）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tags FROM projects WHERE tags != ''")
    rows = cursor.fetchall()
    conn.close()
    
    all_tags = set()
    for row in rows:
        for tag in (row["tags"] or "").split(","):
            tag = tag.strip()
            if tag:
                all_tags.add(tag)
    return sorted(all_tags)