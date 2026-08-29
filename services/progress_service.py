"""进度记录业务逻辑"""
import json
from datetime import date, timedelta
from typing import List, Optional
from database import get_connection, row_to_progress
from models import ProgressRecord
from config import (
    PROGRESS_LINEAR, PROGRESS_HIERARCHICAL, PROGRESS_PERCENTAGE,
    STATUS_IN_PROGRESS
)


class ProgressService:

    def create(self, record: ProgressRecord) -> ProgressRecord:
        """创建进度记录并更新项目总进度"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO progress_records (project_id, record_date,
                start_value, end_value, module_index, module_name,
                part_start, part_end, total_parts, progress_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.project_id,
            record.record_date.isoformat(),
            record.start_value,
            record.end_value,
            record.module_index,
            record.module_name,
            record.part_start,
            record.part_end,
            record.total_parts,
            record.progress_note,
        ))

        conn.commit()
        record.id = cursor.lastrowid

        # 更新项目总进度和活跃日期
        self._update_project_progress(cursor, record.project_id)
        cursor.execute("""
            UPDATE projects SET 
                last_active_date=?,
                status=CASE WHEN status='backlog' THEN ? ELSE status END,
                updated_at=datetime('now','localtime')
            WHERE id=?
        """, (record.record_date.isoformat(), STATUS_IN_PROGRESS, record.project_id))

        conn.commit()
        conn.close()
        return record

    def _update_project_progress(self, cursor, project_id: int):
        """根据进度类型计算并更新项目总进度百分比"""
        cursor.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        project = cursor.fetchone()
        if not project:
            return

        progress_type = project["progress_type"]

        if progress_type == PROGRESS_LINEAR:
            # 线性型：取最大end_value / total_units
            cursor.execute("""
                SELECT MAX(end_value) as max_progress FROM progress_records
                WHERE project_id=? AND end_value IS NOT NULL
            """, (project_id,))
            row = cursor.fetchone()
            max_val = row["max_progress"] if row["max_progress"] else 0
            total = project["total_units"] or 1
            percent = min(round(max_val / total * 100, 1), 100)

        elif progress_type == PROGRESS_HIERARCHICAL:
            # 层级型：已完成Part数 / 总Part数
            modules = json.loads(project["modules_json"] or "[]")
            if not modules:
                percent = 0
            else:
                total_parts = sum(m["total_parts"] for m in modules)
                # 对每个Module取最大part_end
                completed_parts = 0
                for i, m in enumerate(modules):
                    cursor.execute("""
                        SELECT MAX(part_end) as max_part FROM progress_records
                        WHERE project_id=? AND module_index=? AND part_end IS NOT NULL
                    """, (project_id, i))
                    row = cursor.fetchone()
                    completed_parts += row["max_part"] if row and row["max_part"] else 0
                percent = min(round(completed_parts / total_parts * 100, 1), 100)

        elif progress_type == PROGRESS_PERCENTAGE:
            # 百分比型：取最新记录的手动百分比（暂用end_value字段）
            cursor.execute("""
                SELECT end_value FROM progress_records
                WHERE project_id=? AND end_value IS NOT NULL
                ORDER BY record_date DESC, id DESC LIMIT 1
            """, (project_id,))
            row = cursor.fetchone()
            percent = row["end_value"] if row else 0
        else:
            percent = 0

        cursor.execute(
            "UPDATE projects SET total_progress=? WHERE id=?",
            (percent, project_id)
        )

    def get_by_project(self, project_id: int, limit: int = 20) -> List[ProgressRecord]:
        """获取项目的进度记录列表"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM progress_records
            WHERE project_id=?
            ORDER BY record_date DESC, id DESC
            LIMIT ?
        """, (project_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [row_to_progress(r) for r in rows]

    def get_by_date(self, record_date: date) -> List[ProgressRecord]:
        """获取指定日期的所有进度记录"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM progress_records
            WHERE record_date=?
            ORDER BY id DESC
        """, (record_date.isoformat(),))
        rows = cursor.fetchall()
        conn.close()
        return [row_to_progress(r) for r in rows]

    def delete(self, record_id: int) -> bool:
        """删除进度记录并重新计算项目进度"""
        conn = get_connection()
        cursor = conn.cursor()

        # 获取关联的project_id
        cursor.execute("SELECT project_id FROM progress_records WHERE id=?", (record_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        project_id = row["project_id"]

        cursor.execute("DELETE FROM progress_records WHERE id=?", (record_id,))

        # 重新计算项目进度
        self._update_project_progress(cursor, project_id)

        conn.commit()
        conn.close()
        return True


    def get_by_id(self, record_id: int) -> Optional[ProgressRecord]:
        """根据ID获取进度记录"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM progress_records WHERE id=?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row_to_progress(row)
        return None

    def update(self, record: ProgressRecord) -> bool:
        """更新进度记录"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE progress_records SET
                record_date=?,
                start_value=?,
                end_value=?,
                module_index=?,
                module_name=?,
                part_start=?,
                part_end=?,
                total_parts=?,
                progress_note=?
            WHERE id=?
        """, (
            record.record_date.isoformat(),
            record.start_value,
            record.end_value,
            record.module_index,
            record.module_name,
            record.part_start,
            record.part_end,
            record.total_parts,
            record.progress_note,
            record.id,
        ))
        conn.commit()

        # 重新计算项目总进度
        self._update_project_progress(cursor, record.project_id)
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