"""项目业务逻辑"""
import json
from datetime import date
from typing import List, Optional
from database import get_connection, row_to_project
from models import Project, ModuleInfo
from config import STATUS_BACKLOG, STATUS_IN_PROGRESS, STATUS_DONE


class ProjectService:

    def create(self, project: Project) -> Project:
        """创建项目"""
        conn = get_connection()
        cursor = conn.cursor()

        modules_json = json.dumps(
            [{"name": m.name, "total_parts": m.total_parts} for m in project.modules],
            ensure_ascii=False
        )

        cursor.execute("""
            INSERT INTO projects (name, type, source, url, progress_type,
                total_units, unit_label, modules_json, expected_end_date,
                priority, tags, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project.name,
            project.type,
            project.source,
            project.url,
            project.progress_type,
            project.total_units,
            project.unit_label,
            modules_json,
            project.expected_end_date.isoformat() if project.expected_end_date else None,
            project.priority,
            ",".join(project.tags),
            project.status,
        ))

        conn.commit()
        project.id = cursor.lastrowid
        conn.close()
        return project

    def update(self, project: Project) -> bool:
        """更新项目"""
        conn = get_connection()
        cursor = conn.cursor()

        modules_json = json.dumps(
            [{"name": m.name, "total_parts": m.total_parts} for m in project.modules],
            ensure_ascii=False
        )

        cursor.execute("""
            UPDATE projects SET
                name=?, type=?, source=?, url=?, progress_type=?,
                total_units=?, unit_label=?, modules_json=?,
                expected_end_date=?, priority=?, tags=?, status=?,
                total_progress=?, last_active_date=?,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (
            project.name,
            project.type,
            project.source,
            project.url,
            project.progress_type,
            project.total_units,
            project.unit_label,
            modules_json,
            project.expected_end_date.isoformat() if project.expected_end_date else None,
            project.priority,
            ",".join(project.tags),
            project.status,
            project.total_progress,
            project.last_active_date.isoformat() if project.last_active_date else None,
            project.id,
        ))

        conn.commit()
        conn.close()
        return True

    def delete(self, project_id: int) -> bool:
        """删除项目及其关联数据"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()
        conn.close()
        return True

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row_to_project(row)
        return None

    def get_all(self, status_filter: Optional[str] = None) -> List[Project]:
        """获取所有项目，可选状态过滤"""
        conn = get_connection()
        cursor = conn.cursor()

        if status_filter:
            cursor.execute(
                "SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC",
                (status_filter,)
            )
        else:
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")

        rows = cursor.fetchall()
        conn.close()
        return [row_to_project(r) for r in rows]

    def get_by_status_list(self, status_list: List[str]) -> List[Project]:
        """获取指定状态列表的项目"""
        conn = get_connection()
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(status_list))
        cursor.execute(
            f"SELECT * FROM projects WHERE status IN ({placeholders}) ORDER BY priority DESC, updated_at DESC",
            status_list
        )
        rows = cursor.fetchall()
        conn.close()
        return [row_to_project(r) for r in rows]

    def update_status(self, project_id: int, new_status: str) -> bool:
        """更新项目状态"""
        conn = get_connection()
        cursor = conn.cursor()

        if new_status == STATUS_DONE:
            cursor.execute("""
                UPDATE projects SET status=?, last_active_date=date('now','localtime'),
                    updated_at=datetime('now','localtime'), total_progress=100
                WHERE id=?
            """, (new_status, project_id))
        else:
            cursor.execute("""
                UPDATE projects SET status=?, updated_at=datetime('now','localtime')
                WHERE id=?
            """, (new_status, project_id))

        conn.commit()
        conn.close()
        return True

    def get_last_progress(self, project_id: int) -> Optional[int]:
        """获取项目最近一次进度结束值（线性型用）"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT end_value FROM progress_records
            WHERE project_id=? AND end_value IS NOT NULL
            ORDER BY record_date DESC, id DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["end_value"]
        return None

    def get_module_progress(self, project_id: int, module_index: int) -> Optional[int]:
        """获取层级型项目某个Module最近一次Part结束值"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT part_end FROM progress_records
            WHERE project_id=? AND module_index=? AND part_end IS NOT NULL
            ORDER BY record_date DESC, id DESC
            LIMIT 1
        """, (project_id, module_index))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["part_end"]
        return None
    

    def search(self, keyword: str = "", status_filter: str = None, 
               type_filter: str = None) -> List[Project]:
        '''多条件搜索项目'''
        conn = get_connection()
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if keyword:
            conditions.append("name LIKE ?")
            params.append(f"%{keyword}%")
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if type_filter:
            conditions.append("type = ?")
            params.append(type_filter)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(
            f"SELECT * FROM projects WHERE {where_clause} ORDER BY updated_at DESC",
            params
        )
        rows = cursor.fetchall()
        conn.close()
        return [row_to_project(r) for r in rows]

    def get_last_module_progress(self, project_id: int, module_index: int) -> Optional[int]:
        """获取层级型项目指定Module最近一次Part结束值"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT part_end FROM progress_records
            WHERE project_id=? AND module_index=? AND part_end IS NOT NULL
            ORDER BY record_date DESC, id DESC
            LIMIT 1
        """, (project_id, module_index))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["part_end"]
        return None