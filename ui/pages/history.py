"""完成记录页面 - 周/月/年视图"""
from datetime import date, timedelta
from nicegui import ui
from services.project_service import ProjectService
from config import (
    TYPE_LABELS, STATUS_DONE, STATUS_ARCHIVED,
    PROGRESS_TYPE_LABELS,
)

project_service = ProjectService()


@ui.page("/history")
def history_page():
    """完成记录页面"""
    ui.label("🏆 完成记录").classes("text-2xl font-bold p-4")

    # ─── 视图切换 ───
    with ui.row().classes("items-center gap-4 p-4 flex-wrap"):
        view_toggle = ui.toggle(
            options=["日", "周", "月", "年"],
            value="周",
            on_change=lambda e: render_view()
        ).classes("w-64")

        # 日期导航
        nav_row = ui.row().classes("items-center gap-2")
        current_label = ui.label("").classes("text-lg font-bold mx-4")

    content_area = ui.column().classes("p-4 w-full")

    def render_view():
        """根据选中的视图渲染内容"""
        content_area.clear()
        nav_row.clear()
        view = view_toggle.value
        today = date.today()

        if view == "日":
            _render_day_view(content_area, nav_row, current_label, today)
        elif view == "周":
            _render_week_view(content_area, nav_row, current_label, today)
        elif view == "月":
            _render_month_view(content_area, nav_row, current_label, today)
        elif view == "年":
            _render_year_view(content_area, nav_row, current_label, today)

    # view_toggle.on("change", lambda: render_view()) # to be deleted

    # 初始加载
    render_view()


def _render_day_view(content_area, nav_row, current_label, today):
    """日视图 - 展示和修改某天的完成项目明细"""
    from services.progress_service import ProgressService
    progress_service = ProgressService()

    current_date = {"value": today}

    def update_label():
        d = current_date["value"]
        week_day = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()]
        current_label.set_text(f"{d.isoformat()} {week_day}")

    def prev_day():
        current_date["value"] = current_date["value"] - timedelta(days=1)
        update_label()
        refresh_content()

    def next_day():
        if current_date["value"] < today:
            current_date["value"] = current_date["value"] + timedelta(days=1)
            update_label()
            refresh_content()

    def go_today():
        current_date["value"] = today
        update_label()
        refresh_content()

    with nav_row:
        ui.button("◀", on_click=prev_day).props("size=sm flat dense")
        ui.button("今天", on_click=go_today).props("size=sm flat")
        ui.button("▶", on_click=next_day).props("size=sm flat dense")

    update_label()

    def refresh_content():
        content_area.clear()
        d = current_date["value"]

        # 获取当日完成的进度记录
        day_records = progress_service.get_by_date(d)
        # 获取当天完成的项目（状态为done/archived且最后活跃日期为当天）
        completed_projects = _get_completed_on_date(d)

        with content_area:
            # ─── 当日完成的项目 ───
            ui.label("✅ 当日完成的项目").classes("font-bold text-lg mb-3")
            if not completed_projects:
                ui.label("当天没有完成的项目").classes("text-gray-400 text-sm p-4")
            else:
                for p in completed_projects:
                    _render_completed_project_card(p, d, progress_service, refresh_content)

            # ─── 当日有进度的项目 ───
            ui.separator()
            ui.label("📝 当日有进度的项目").classes("font-bold text-lg mb-3 mt-4")

            if not day_records:
                ui.label("当天没有进度记录").classes("text-gray-400 text-sm p-4")
            else:
                # 按项目分组
                project_records = {}
                for r in day_records:
                    if r.project_id not in project_records:
                        project_records[r.project_id] = []
                    project_records[r.project_id].append(r)

                for project_id, records in project_records.items():
                    proj = project_service.get_by_id(project_id)
                    if not proj:
                        continue
                    _render_day_progress_card(proj, records, d)

    refresh_content()


def _render_week_view(content_area, nav_row, current_label, today):
    """本周视图"""
    # 计算本周范围
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    # 存储当前周的周一日期，用于翻页
    week_start = {"value": monday}

    def update_week():
        m = week_start["value"]
        s = m + timedelta(days=6)
        current_label.set_text(f"{m.strftime('%Y/%m/%d')} - {s.strftime('%Y/%m/%d')}")

    def prev_week():
        week_start["value"] = week_start["value"] - timedelta(days=7)
        update_week()
        refresh_list(week_start["value"], week_start["value"] + timedelta(days=6))

    def next_week():
        new_start = week_start["value"] + timedelta(days=7)
        if new_start <= today:
            week_start["value"] = new_start
            update_week()
            refresh_list(week_start["value"], week_start["value"] + timedelta(days=6))

    with nav_row:
        ui.button("◀", on_click=prev_week).props("size=sm flat dense")
        ui.button("▶", on_click=next_week).props("size=sm flat dense")

    update_week()

    def refresh_list(start, end):
        content_area.clear()
        with content_area:
            projects = _get_completed_in_range(start, end)
            if not projects:
                ui.label("本周暂无完成项目").classes("text-gray-400 p-8 text-center w-full")
                return
            ui.label(f"共完成 {len(projects)} 项").classes("text-sm text-gray-500 mb-4")
            for p in projects:
                _render_project_card(p)

    refresh_list(monday, sunday)


def _render_month_view(content_area, nav_row, current_label, today):
    """本月视图"""
    current_month = {"year": today.year, "month": today.month}

    def update_month():
        current_label.set_text(f"{current_month['year']}年{current_month['month']}月")

    def prev_month():
        if current_month["month"] == 1:
            current_month["year"] -= 1
            current_month["month"] = 12
        else:
            current_month["month"] -= 1
        update_month()
        refresh_list()

    def next_month():
        if (current_month["year"] < today.year or
            (current_month["year"] == today.year and current_month["month"] < today.month)):
            if current_month["month"] == 12:
                current_month["year"] += 1
                current_month["month"] = 1
            else:
                current_month["month"] += 1
            update_month()
            refresh_list()

    with nav_row:
        ui.button("◀", on_click=prev_month).props("size=sm flat dense")
        ui.button("▶", on_click=next_month).props("size=sm flat dense")

    update_month()

    def refresh_list():
        content_area.clear()
        with content_area:
            y = current_month["year"]
            m = current_month["month"]
            start = date(y, m, 1)
            if m == 12:
                end = date(y + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(y, m + 1, 1) - timedelta(days=1)

            projects = _get_completed_in_range(start, end)

            if not projects:
                ui.label("本月暂无完成项目").classes("text-gray-400 p-8 text-center w-full")
                return

            # 统计
            books = [p for p in projects if p.type == "book"]
            courses = [p for p in projects if p.type == "course"]
            others = [p for p in projects if p.type == "other"]
            total_pages = sum(p.total_units or 0 for p in books)

            with ui.row().classes("gap-4 mb-4"):
                with ui.card().classes("flex-1 p-3 text-center"):
                    ui.label(f"共 {len(projects)} 项").classes("text-2xl font-bold")
                    ui.label("完成项目").classes("text-xs text-gray-500")
                if books:
                    with ui.card().classes("flex-1 p-3 text-center"):
                        ui.label(f"{len(books)} 本 / {total_pages}页").classes("text-lg font-bold")
                        ui.label("书籍").classes("text-xs text-gray-500")
                if courses:
                    with ui.card().classes("flex-1 p-3 text-center"):
                        ui.label(f"{len(courses)} 门").classes("text-lg font-bold")
                        ui.label("课程").classes("text-xs text-gray-500")

            ui.separator()

            # 按周分组
            weeks = {}
            for p in projects:
                if p.last_active_date:
                    d = p.last_active_date
                    week_num = d.isocalendar()[1]
                    if week_num not in weeks:
                        weeks[week_num] = []
                    weeks[week_num].append(p)

            for week_num in sorted(weeks.keys(), reverse=True):
                items = weeks[week_num]
                # 获取该周的日期范围
                ws = date.fromisocalendar(y, week_num, 1)
                we = ws + timedelta(days=6)
                with ui.expansion(f"第{week_num}周 ({ws.strftime('%m/%d')}-{we.strftime('%m/%d')}) — {len(items)}项",
                                  icon="calendar_view_week").classes("w-full"):
                    for p in items:
                        _render_project_card(p)

    refresh_list()


def _render_year_view(content_area, nav_row, current_label, today):
    """本年视图"""
    current_year = {"value": today.year}

    def update_year():
        current_label.set_text(f"{current_year['value']}年")

    def prev_year():
        current_year["value"] -= 1
        update_year()
        refresh_list()

    def next_year():
        if current_year["value"] < today.year:
            current_year["value"] += 1
            update_year()
            refresh_list()

    with nav_row:
        ui.button("◀", on_click=prev_year).props("size=sm flat dense")
        ui.button("▶", on_click=next_year).props("size=sm flat dense")

    update_year()

    def refresh_list():
        content_area.clear()
        y = current_year["value"]
        start = date(y, 1, 1)
        end = date(y, 12, 31)

        projects = _get_completed_in_range(start, end)

        with content_area:
            if not projects:
                ui.label("本年暂无完成项目").classes("text-gray-400 p-8 text-center w-full")
                return

            # 统计卡片
            books_count = len([p for p in projects if p.type == "book"])
            courses_count = len([p for p in projects if p.type == "course"])
            others_count = len([p for p in projects if p.type == "other"])

            with ui.row().classes("gap-4 mb-4"):
                with ui.card().classes("flex-1 p-3 text-center"):
                    ui.label(str(len(projects))).classes("text-2xl font-bold")
                    ui.label("总计").classes("text-xs text-gray-500")
                with ui.card().classes("flex-1 p-3 text-center"):
                    ui.label(str(books_count)).classes("text-2xl font-bold")
                    ui.label("📖 书籍").classes("text-xs text-gray-500")
                with ui.card().classes("flex-1 p-3 text-center"):
                    ui.label(str(courses_count)).classes("text-2xl font-bold")
                    ui.label("🎓 课程").classes("text-xs text-gray-500")

            ui.separator()

            # 按月份分组 — 时间轴样式
            months = {}
            for p in projects:
                if p.last_active_date:
                    month_key = p.last_active_date.month
                    if month_key not in months:
                        months[month_key] = []
                    months[month_key].append(p)

            for month_num in sorted(months.keys(), reverse=True):
                items = months[month_num]
                month_name = f"{month_num}月"
                with ui.expansion(f"── {month_name} ── ({len(items)}项)", icon="calendar_month").classes("w-full"):
                    for p in sorted(items, key=lambda x: x.last_active_date, reverse=True):
                        _render_project_card(p, show_date=True)

    refresh_list()


# ─── 辅助函数 ───

def _get_completed_in_range(start: date, end: date) -> list:
    """获取指定日期范围内完成的项目"""
    all_done = project_service.get_by_status_list([STATUS_DONE, STATUS_ARCHIVED])
    result = []
    for p in all_done:
        if p.last_active_date and start <= p.last_active_date <= end:
            result.append(p)
    return sorted(result, key=lambda x: x.last_active_date, reverse=True)


def _get_completed_on_date(d: date) -> list:
    """获取指定日期完成的项目（状态为done/archived且最后活跃日期为该日期）"""
    all_done = project_service.get_by_status_list([STATUS_DONE, STATUS_ARCHIVED])
    return [p for p in all_done if p.last_active_date and p.last_active_date == d]


def _render_completed_project_card(project, display_date, progress_service, refresh_fn):
    """渲染已完成项目卡片（含撤销和修改日期功能）"""
    icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(project.type, "📌")

    with ui.card().classes("w-full mb-2 p-3"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"{icon}").classes("text-lg")
                ui.label(project.name).classes("font-bold")
            ui.label(f"完成于 {display_date}").classes("text-xs text-gray-500")

        # 进度信息
        if project.total_units:
            ui.label(f"共 {project.total_units} {project.unit_label or '页'}").classes("text-xs text-gray-500")
        if project.modules:
            total_parts = sum(m.total_parts for m in project.modules)
            ui.label(f"{len(project.modules)} Module / {total_parts} Part").classes("text-xs text-gray-500")

        ui.linear_progress(value=1, show_value=False).classes("w-full mt-2")
        ui.label("100%").classes("text-xs text-green-500")

        # 操作按钮
        with ui.row().classes("gap-2 mt-2"):
            # 修改完成日期
            ui.button("修改完成日期", on_click=lambda p=project: _show_date_picker(p, refresh_fn), icon="edit_calendar") \
                .props("size=sm flat")

            # 撤销完成
            def undo_complete(p=project):
                from config import STATUS_IN_PROGRESS
                project_service.update_status(p.id, STATUS_IN_PROGRESS)
                ui.notify(f"「{p.name}」已退回进行中", type="warning")
                refresh_fn()

            ui.button("撤销完成", on_click=undo_complete, icon="undo") \
                .props("size=sm flat color=orange")


def _show_date_picker(project, refresh_fn):
    """显示日期选择对话框，修改完成日期"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"修改「{project.name}」的完成日期").classes("text-lg font-bold mb-4")
        ui.label(f"当前完成日期：{project.last_active_date}").classes("text-sm text-gray-500 mb-2")

        new_date_input = ui.date(
            value=str(project.last_active_date) if project.last_active_date else str(date.today())
        ).classes("w-full")

        with ui.row().classes("gap-2 justify-end mt-4"):
            ui.button("取消", on_click=dialog.close)

            def save_date():
                from datetime import datetime
                new_date_str = new_date_input.value
                if new_date_str:
                    new_date = date.fromisoformat(new_date_str)
                    project.last_active_date = new_date
                    project_service.update(project)
                    ui.notify(f"完成日期已更新为 {new_date}", type="positive")
                    dialog.close()
                    refresh_fn()

            ui.button("保存", on_click=save_date, icon="save").classes("bg-blue-500 text-white")
    dialog.open()


def _render_day_progress_card(project, records, display_date):
    """渲染当日进度明细卡片"""
    icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(project.type, "📌")

    with ui.card().classes("w-full mb-2 p-3"):
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{icon}").classes("text-lg")
            ui.label(project.name).classes("font-bold")
            ui.label(f"当前总进度 {project.total_progress}%").classes("text-xs text-gray-500 ml-auto")

        ui.linear_progress(value=project.total_progress / 100).classes("w-full mt-1")

        # 当日进度记录
        for r in records:
            with ui.row().classes("gap-2 text-sm text-gray-600 mt-2"):
                if r.start_value and r.end_value:
                    total = project.total_units or "?"
                    unit = project.unit_label or "页"
                    ui.label(f"📖 P{r.start_value}-{r.end_value}/{total}{unit}")
                elif r.module_name:
                    ui.label(f"🎓 {r.module_name} Part {r.part_start}-{r.part_end}/{r.total_parts}")
                else:
                    ui.label(f"📌 进度更新至 {r.end_value}%")
                if r.progress_note:
                    ui.label(f"💬 {r.progress_note}").classes("text-xs text-gray-400")

def _render_project_card(project, show_date=False):
    """渲染完成项目卡片"""
    icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(project.type, "📌")

    with ui.card().classes("w-full mb-2 p-3"):
        with ui.row().classes("items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                ui.label(f"{icon}").classes("text-lg")
                ui.label(project.name).classes("font-bold")

            if show_date and project.last_active_date:
                ui.label(f"完成于 {project.last_active_date}").classes("text-xs text-gray-500")

        with ui.row().classes("gap-2 mt-1 flex-wrap"):
            ui.label(TYPE_LABELS.get(project.type, "")).classes("text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded")
            ui.label(PROGRESS_TYPE_LABELS.get(project.progress_type, "")).classes("text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded")
            if project.total_units:
                ui.label(f"共{project.total_units}{project.unit_label or '页'}").classes("text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded")
            if project.modules:
                total_parts = sum(m.total_parts for m in project.modules)
                ui.label(f"{len(project.modules)}Module / {total_parts}Part").classes("text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded")

        # 进度条
        ui.linear_progress(value=100 / 100, show_value=False).classes("w-full mt-2")
        ui.label("100%").classes("text-xs text-green-500")

        # 标签
        if project.tags:
            with ui.row().classes("gap-1 mt-1"):
                for tag in project.tags[:5]:
                    ui.label(tag).classes("text-xs bg-gray-50 text-gray-500 px-1.5 py-0.5 rounded")