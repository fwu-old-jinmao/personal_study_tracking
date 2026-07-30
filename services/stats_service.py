"""统计服务"""
from datetime import date, timedelta
from typing import List, Dict, Optional
from database import get_connection
from config import STATUS_DONE, STATUS_ARCHIVED, STATUS_IN_PROGRESS


class StatsService:

    def get_active_project_count(self) -> int:
        """进行中的项目数"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM projects WHERE status=?",
            (STATUS_IN_PROGRESS,)
        )
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_paused_project_count(self) -> int:
        """暂缓的项目数"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM projects WHERE status='paused'"
        )
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_backlog_project_count(self) -> int:
        """规划中的项目数"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM projects WHERE status='backlog'"
        )
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_weekly_completed_count(self, target_date: date = None) -> int:
        """本周完成的项目数"""
        if target_date is None:
            target_date = date.today()
        monday = target_date - timedelta(days=target_date.weekday())
        sunday = monday + timedelta(days=6)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM projects
            WHERE status IN (?, ?)
            AND last_active_date BETWEEN ? AND ?
        """, (STATUS_DONE, STATUS_ARCHIVED, monday.isoformat(), sunday.isoformat()))
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_monthly_completed_count(self, year: int = None, month: int = None) -> int:
        """本月完成的项目数"""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM projects
            WHERE status IN (?, ?)
            AND last_active_date BETWEEN ? AND ?
        """, (STATUS_DONE, STATUS_ARCHIVED, start_date.isoformat(), end_date.isoformat()))
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_consecutive_active_days(self) -> int:
        """计算连续活跃天数（从今天往前数）"""
        conn = get_connection()
        cursor = conn.cursor()

        # 获取所有有进度记录的日期
        cursor.execute("""
            SELECT DISTINCT record_date FROM progress_records
            ORDER BY record_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return 0

        active_dates = set()
        for row in rows:
            try:
                active_dates.add(date.fromisoformat(row["record_date"]))
            except (ValueError, TypeError):
                pass

        today = date.today()
        consecutive = 0
        check_date = today

        # 先检查今天
        if today in active_dates:
            consecutive = 1
            check_date = today - timedelta(days=1)
            while check_date in active_dates:
                consecutive += 1
                check_date -= timedelta(days=1)
        else:
            # 今天没有，从昨天开始检查
            check_date = today - timedelta(days=1)
            if check_date in active_dates:
                consecutive = 1
                check_date -= timedelta(days=1)
                while check_date in active_dates:
                    consecutive += 1
                    check_date -= timedelta(days=1)

        return consecutive

    def get_daily_progress_trend(self, days: int = 30) -> List[Dict]:
        """获取每日推进量趋势（用于图表）"""
        conn = get_connection()
        cursor = conn.cursor()
        start_date = (date.today() - timedelta(days=days - 1)).isoformat()

        cursor.execute("""
            SELECT record_date,
                   SUM(CASE WHEN end_value IS NOT NULL AND start_value IS NOT NULL
                       THEN end_value - start_value + 1 ELSE 0 END) as daily_units,
                   COUNT(DISTINCT project_id) as project_count
            FROM progress_records
            WHERE record_date >= ?
            GROUP BY record_date
            ORDER BY record_date
        """, (start_date,))
        rows = cursor.fetchall()
        conn.close()

        # 填充没有记录的日期
        result = []
        current = date.today() - timedelta(days=days - 1)
        data_map = {}
        for row in rows:
            data_map[row["record_date"]] = {
                "units": row["daily_units"] or 0,
                "projects": row["project_count"] or 0
            }

        for i in range(days):
            d = current + timedelta(days=i)
            d_str = d.isoformat()
            if d_str in data_map:
                result.append({
                    "date": d_str,
                    "units": data_map[d_str]["units"],
                    "projects": data_map[d_str]["projects"]
                })
            else:
                result.append({"date": d_str, "units": 0, "projects": 0})

        return result

    def get_category_distribution(self) -> List[Dict]:
        """获取已完成项目的类别分布"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT type, COUNT(*) as cnt
            FROM projects
            WHERE status IN (?, ?)
            GROUP BY type
        """, (STATUS_DONE, STATUS_ARCHIVED))
        rows = cursor.fetchall()
        conn.close()
        return [{"type": r["type"], "count": r["cnt"]} for r in rows]

    def get_yearly_heatmap(self, year: int = None) -> List[Dict]:
        """获取年度活跃热力图数据"""
        if year is None:
            year = date.today().year

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT record_date,
                   SUM(CASE WHEN end_value IS NOT NULL AND start_value IS NOT NULL
                       THEN end_value - start_value + 1 ELSE 0 END) as daily_units
            FROM progress_records
            WHERE record_date BETWEEN ? AND ?
            GROUP BY record_date
            ORDER BY record_date
        """, (f"{year}-01-01", f"{year}-12-31"))
        rows = cursor.fetchall()
        conn.close()

        return [
            {"date": r["record_date"], "value": r["daily_units"] or 0}
            for r in rows
        ]

    def get_monthly_completed(self, year: int, month: int) -> List[Dict]:
        """获取指定月份完成的项目（保留原有方法）"""
        conn = get_connection()
        cursor = conn.cursor()
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        cursor.execute("""
            SELECT * FROM projects
            WHERE status IN (?, ?)
            AND last_active_date BETWEEN ? AND ?
            ORDER BY last_active_date DESC
        """, (STATUS_DONE, STATUS_ARCHIVED, start_date.isoformat(), end_date.isoformat()))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_yearly_completed(self, year: int) -> List[Dict]:
        """获取指定年份完成的项目（保留原有方法）"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM projects
            WHERE status IN (?, ?)
            AND last_active_date BETWEEN ? AND ?
            ORDER BY last_active_date DESC
        """, (STATUS_DONE, STATUS_ARCHIVED, f"{year}-01-01", f"{year}-12-31"))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]