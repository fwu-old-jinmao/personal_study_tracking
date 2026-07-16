"""Kanban看板页面"""
from nicegui import ui
from services.project_service import ProjectService
from config import (
    STATUS_BACKLOG, STATUS_IN_PROGRESS, STATUS_PAUSED, STATUS_DONE, STATUS_ARCHIVED,
    STATUS_LABELS, TYPE_OPTIONS, TYPE_LABELS, DONE_RETENTION_DAYS,
)
from ui.components.project_card import ProjectCard

project_service = ProjectService()


@ui.page("/kanban")
def kanban_page():
    """看板页面"""

    # 页面标题和筛选
    with ui.row().classes("items-center gap-4 p-4 w-full"):
        ui.label("📌 项目看板").classes("text-2xl font-bold")
        ui.space()

        type_filter = ui.select(
            label="筛选类型",
            options=["全部"] + [TYPE_LABELS[t] for t in TYPE_OPTIONS],
            value="全部"
        ).classes("w-32")

    def on_type_filter_change():
        """类型筛选变化时刷新所有列"""
        refresh_all_columns()

    type_filter.on("change", on_type_filter_change)

    # 看板列定义
    columns_def = [
        {"status": STATUS_BACKLOG, "color": "bg-gray-50", "border": "border-gray-200"},
        {"status": STATUS_IN_PROGRESS, "color": "bg-blue-50", "border": "border-blue-200"},
        {"status": STATUS_PAUSED, "color": "bg-yellow-50", "border": "border-yellow-200"},
        {"status": STATUS_DONE, "color": "bg-green-50", "border": "border-green-200"},
    ]

    # 列容器引用
    column_containers = {}

    # 看板主体
    with ui.row().classes("w-full gap-4 p-4 overflow-x-auto flex-nowrap") as kanban_row:
        kanban_row.style("min-height: 400px")

        for col_def in columns_def:
            status = col_def["status"]
            with ui.column().classes(
                f"flex-1 min-w-[240px] max-w-[320px] {col_def['color']} "
                f"rounded-lg p-3 border {col_def['border']}"
            ) as col:
                column_containers[status] = col
                ui.label(STATUS_LABELS[status]).classes("font-bold text-lg mb-3")

                # 项目卡片容器
                cards_container = ui.column().classes("w-full gap-2")
                setattr(col, "cards_container", cards_container)

    # 独立显示已归档（不在主看板列中）
    with ui.expansion("📦 已归档项目", icon="archive").classes("w-full p-4"):
        archived_container = ui.column().classes("w-full gap-2")

    def refresh_all_columns():
        """刷新所有列的项目"""
        # 获取类型筛选值
        type_val = _get_type_value(type_filter.value)

        for col_def in columns_def:
            status = col_def["status"]
            col = column_containers[status]
            cards_container = col.cards_container
            cards_container.clear()

            projects = project_service.get_by_status_list([status])
            # 应用类型筛选
            if type_val:
                projects = [p for p in projects if p.type == type_val]

            with cards_container:
                if not projects:
                    ui.label("—").classes("text-gray-400 text-sm p-4 text-center w-full")
                else:
                    for p in projects:
                        card = ProjectCard(
                            project=p,
                            on_status_change=handle_status_change,
                            on_click=lambda pid: ui.notify(f"项目详情功能将在后续版本实现 (ID: {pid})")
                        )
                        card.render()

        # 刷新归档区
        archived_container.clear()
        archived_projects = project_service.get_by_status_list([STATUS_ARCHIVED])
        if type_val:
            archived_projects = [p for p in archived_projects if p.type == type_val]
        with archived_container:
            if not archived_projects:
                ui.label("暂无已归档项目").classes("text-gray-400 text-sm p-4")
            else:
                for p in archived_projects:
                    ui.label(f"📌 {p.name} - 完成于 {p.last_active_date}").classes("text-sm text-gray-500 p-1")

        ui.update()

    def handle_status_change(project_id: int, new_status: str):
        """处理状态变更"""
        project = project_service.get_by_id(project_id)
        if not project:
            return

        old_status = project.status
        project_service.update_status(project_id, new_status)

        status_text = STATUS_LABELS.get(new_status, new_status)
        ui.notify(f"「{project.name}」→ {status_text}", type="positive")

        refresh_all_columns()

    def _get_type_value(label: str) -> str | None:
        """将类型标签转换为类型值"""
        if label == "全部":
            return None
        for k, v in TYPE_LABELS.items():
            if v == label:
                return k
        return None

    # 初始加载
    refresh_all_columns()