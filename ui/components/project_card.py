"""看板项目卡片组件"""
from nicegui import ui
from models import Project
from config import TYPE_LABELS, PRIORITY_LABELS


class ProjectCard:
    """项目卡片，用于看板展示"""

    def __init__(self, project: Project, on_status_change=None, on_click=None):
        self.project = project
        self.on_status_change = on_status_change
        self.on_click = on_click

    def render(self):
        """渲染卡片"""
        with ui.card().classes("w-full mb-2 p-3 cursor-pointer hover:shadow-md transition-shadow"):
            # 点击卡片跳转详情
            if self.on_click:
                self.card_element = ui.element("div").classes("w-full")
                self.card_element.on("click", lambda: self.on_click(self.project.id))

            # 标题行
            with ui.row().classes("items-center gap-2 w-full"):
                icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(self.project.type, "📌")
                ui.label(f"{icon} {self.project.name}").classes("font-bold text-sm flex-1")

            # 标签行
            with ui.row().classes("gap-1 mt-1 flex-wrap"):
                ui.label(TYPE_LABELS.get(self.project.type, "")).classes("text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded")
                if self.project.priority == "high":
                    ui.label("高优先").classes("text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded")
                if self.project.source and self.project.source != "other":
                    ui.label(self.project.source).classes("text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded")

            # 进度信息
            if self.project.progress_type == "linear":
                total = self.project.total_units or "?"
                unit = self.project.unit_label or "页"
                ui.label(f"总{total}{unit}").classes("text-xs text-gray-500 mt-1")
            elif self.project.progress_type == "hierarchical":
                module_count = len(self.project.modules)
                total_parts = sum(m.total_parts for m in self.project.modules)
                ui.label(f"{module_count}个Module / {total_parts}个Part").classes("text-xs text-gray-500 mt-1")

            # 进度条
            ui.linear_progress(value=self.project.total_progress / 100).classes("w-full mt-1")
            ui.label(f"{self.project.total_progress}%").classes("text-xs text-gray-500")

            # 底部信息
            with ui.row().classes("gap-2 text-xs text-gray-400 mt-1"):
                if self.project.last_active_date:
                    ui.label(f"最后活跃: {self.project.last_active_date}")
                if self.project.expected_end_date:
                    ui.label(f"预计完成: {self.project.expected_end_date}")

            # 状态操作按钮（由外部传入的回调控制）
            if self.on_status_change:
                with ui.row().classes("gap-1 mt-2"):
                    self._render_action_buttons()

    def _render_action_buttons(self):
        """根据当前状态渲染操作按钮"""
        from config import (
            STATUS_BACKLOG, STATUS_IN_PROGRESS, STATUS_PAUSED,
            STATUS_DONE, STATUS_ARCHIVED
        )

        status = self.project.status

        if status == STATUS_BACKLOG:
            ui.button("开始", on_click=lambda: self.on_status_change(self.project.id, STATUS_IN_PROGRESS)) \
                .props("size=sm color=green flat")
            # 暂不支持从backlog直接暂停，逻辑上应该先开始
            # 但允许直接归档（放弃该项目）
            ui.button("放弃", on_click=lambda: self.on_status_change(self.project.id, STATUS_ARCHIVED)) \
                .props("size=sm color=gray flat")

        elif status == STATUS_IN_PROGRESS:
            ui.button("暂停", on_click=lambda: self.on_status_change(self.project.id, STATUS_PAUSED)) \
                .props("size=sm color=orange flat")
            ui.button("推进", on_click=lambda: ui.navigate.to(f"/log?project={self.project.id}")) \
                .props("size=sm color=green flat")
            ui.button("完成", on_click=lambda: self.on_status_change(self.project.id, STATUS_DONE)) \
                .props("size=sm color=blue flat")

        elif status == STATUS_PAUSED:
            ui.button("继续", on_click=lambda: self.on_status_change(self.project.id, STATUS_IN_PROGRESS)) \
                .props("size=sm color=green flat")
            ui.button("放弃", on_click=lambda: self.on_status_change(self.project.id, STATUS_ARCHIVED)) \
                .props("size=sm color=gray flat")

        elif status == STATUS_DONE:
            ui.button("归档", on_click=lambda: self.on_status_change(self.project.id, STATUS_ARCHIVED)) \
                .props("size=sm color=purple flat")

        # ARCHIVED 状态不显示操作按钮