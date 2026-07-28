"""项目管理页面 - 项目列表、创建、编辑"""
import json
from datetime import date
from nicegui import ui
from models import Project, ModuleInfo
from services.project_service import ProjectService
from database import get_all_tags
from config import (
    TYPE_OPTIONS, TYPE_LABELS,
    SOURCE_OPTIONS, SOURCE_LABELS,
    PROGRESS_TYPE_OPTIONS, PROGRESS_TYPE_LABELS,
    PROGRESS_LINEAR, PROGRESS_HIERARCHICAL, PROGRESS_PERCENTAGE,
    PRIORITY_OPTIONS, PRIORITY_LABELS,
    STATUS_OPTIONS, STATUS_LABELS,
    STATUS_BACKLOG, STATUS_IN_PROGRESS, STATUS_PAUSED, STATUS_DONE, STATUS_ARCHIVED,
)

project_service = ProjectService()


# ─── 辅助转换函数（放在外部避免闭包冲突）───

def _status_label_to_value(label: str) -> str | None:
    """将状态标签转换为状态值"""
    if label == "全部":
        return None
    for k, v in STATUS_LABELS.items():
        if v == label:
            return k
    return None


def _type_label_to_value(label: str) -> str | None:
    """将类型标签转换为类型值"""
    if label == "全部":
        return None
    for k, v in TYPE_LABELS.items():
        if v == label:
            return k
    return None


def _source_label_to_value(label: str) -> str:
    """将来源标签转换为来源值"""
    for k, v in SOURCE_LABELS.items():
        if v == label:
            return k
    return "other"


def _priority_label_to_value(label: str) -> str:
    """将优先级标签转换为优先级值"""
    for k, v in PRIORITY_LABELS.items():
        if v == label:
            return k
    return "medium"


def _progress_type_label_to_value(label: str) -> str:
    """将进度类型标签转换为进度类型值"""
    for k, v in PROGRESS_TYPE_LABELS.items():
        if v == label:
            return k
    return PROGRESS_LINEAR


# ─── 页面定义 ───

@ui.page("/projects")
def projects_page():
    """项目管理页面"""
    ui.label("📁 项目管理").classes("text-2xl font-bold p-4")

    # ─── 状态变量 ───
    project_list_container = ui.column().classes("p-4 gap-2 w-full")

    # ─── 刷新列表函数（较早定义，因为多处引用）───

    def refresh_list():
        """刷新项目列表"""
        project_list_container.clear()

        keyword = search_input.value or ""
        status_val = _status_label_to_value(status_filter.value)
        type_val = _type_label_to_value(type_filter.value)

        projects = project_service.search(keyword, status_val, type_val)

        with project_list_container:
            if not projects:
                ui.label("暂无项目，点击右上角创建").classes("text-gray-400 p-8 text-center w-full")
                return

            # 表头
            with ui.row().classes("w-full px-4 py-2 bg-gray-100 rounded-t font-bold text-sm"):
                ui.label("项目名称").classes("flex-1")
                ui.label("类型").classes("w-16 text-center")
                ui.label("进度").classes("w-32 text-center")
                ui.label("状态").classes("w-20 text-center")
                ui.label("优先级").classes("w-16 text-center")
                ui.label("最后活跃").classes("w-24 text-center")
                ui.label("操作").classes("w-24 text-center")

            for p in projects:
                _render_project_row(p)

    def _render_project_row(p: Project):
        """渲染单个项目行"""
        icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(p.type, "📌")
        with ui.row().classes("w-full px-4 py-2 border-b items-center hover:bg-gray-50 text-sm"):
            ui.label(f"{icon} {p.name}").classes("flex-1 font-medium")
            ui.label(TYPE_LABELS.get(p.type, "")).classes("w-16 text-center text-xs bg-blue-50 rounded px-1")
            ui.label(f"{p.total_progress}%").classes("w-32 text-center")
            ui.label(STATUS_LABELS.get(p.status, "")).classes("w-20 text-center")
            prio_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(p.priority, "")
            ui.label(prio_icon).classes("w-16 text-center")
            ui.label(str(p.last_active_date) if p.last_active_date else "-").classes("w-24 text-center text-xs text-gray-500")
            with ui.row().classes("w-24 justify-center gap-1"):
                ui.button("", on_click=lambda pid=p.id: open_edit_dialog(pid), icon="edit") \
                    .props("size=sm flat dense")
                ui.button("", on_click=lambda pid=p.id: confirm_delete(pid), icon="delete") \
                    .props("size=sm flat dense color=red")

    # ─── 删除相关 ───

    def confirm_delete(project_id: int):
        """确认删除对话框"""
        project = project_service.get_by_id(project_id)
        if not project:
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"确认删除「{project.name}」？").classes("text-lg font-bold")
            ui.label("删除后所有进度记录和笔记也会被删除，此操作不可恢复。").classes("text-sm text-red-500")
            with ui.row().classes("gap-2 justify-end mt-4"):
                ui.button("取消", on_click=dialog.close)
                ui.button("确认删除", on_click=lambda: _do_delete(project_id, dialog), color="red")
        dialog.open()

    def _do_delete(project_id: int, dialog):
        """执行删除"""
        project_service.delete(project_id)
        dialog.close()
        ui.notify("项目已删除", type="warning")
        refresh_list()

    # ─── 创建/编辑弹窗（必须在工具栏按钮之前定义）───

    def open_create_dialog():
        """打开新建项目弹窗"""
        _open_project_form()

    def open_edit_dialog(project_id: int):
        """打开编辑项目弹窗"""
        project = project_service.get_by_id(project_id)
        if project:
            _open_project_form(project)

    def _open_project_form(project: Project = None):
        """项目表单弹窗（新建/编辑通用）"""
        is_edit = project is not None
        title = f"编辑项目: {project.name}" if is_edit else "新建项目"

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg"):
            ui.label(title).classes("text-xl font-bold mb-4")

            # 基本信息
            name_input = ui.input("项目名称 *", value=project.name if project else "") \
                .classes("w-full")

            with ui.row().classes("gap-4 w-full"):
                type_select = ui.select(
                    options=[TYPE_LABELS[t] for t in TYPE_OPTIONS],
                    label="类型",
                    value=TYPE_LABELS.get(project.type, "书籍") if project else "书籍"
                ).classes("flex-1")

                source_select = ui.select(
                    options=[SOURCE_LABELS[s] for s in SOURCE_OPTIONS],
                    label="来源",
                    value=SOURCE_LABELS.get(project.source, "其他") if project else "其他"
                ).classes("flex-1")

            url_input = ui.input("链接(可选)", value=project.url if project else "") \
                .classes("w-full")

            # 进度类型设置
            ui.separator()
            ui.label("进度设置").classes("font-bold")

            progress_type_options = [PROGRESS_TYPE_LABELS[t] for t in PROGRESS_TYPE_OPTIONS]
            default_pt = PROGRESS_TYPE_LABELS[PROGRESS_LINEAR]  # 默认：线性型 (页数/集数)
            if project and project.progress_type in PROGRESS_TYPE_LABELS:
                default_pt = PROGRESS_TYPE_LABELS[project.progress_type]

            # progress_type_options = [PROGRESS_TYPE_LABELS[t] for t in PROGRESS_TYPE_OPTIONS]
            # default_pt = PROGRESS_TYPE_LABELS.get(project.progress_type, PROGRESS_TYPE_LABELS[PROGRESS_LINEAR])  if project else PROGRESS_TYPE_LABELS[PROGRESS_LINEAR]
            progress_type_select = ui.select(
                options=progress_type_options,
                label="进度类型",
                value=default_pt
            ).classes("w-full")

            # 线性型配置
            linear_config = ui.column().classes("w-full")
            total_units_input = None
            unit_label_input = None

            # 层级型配置
            hierarchical_config = ui.column().classes("w-full")
            modules_container = None

            # 存储模块数据
            module_data = []
            if project and project.modules:
                module_data = [{"name": m.name, "parts": m.total_parts} for m in project.modules]

            def _update_module_name(idx: int, new_name):
                """更新Module名称"""
                if 0 <= idx < len(module_data):
                    module_data[idx]["name"] = new_name

            def _update_module_parts(idx: int, new_parts):
                """更新Module Part数"""
                if 0 <= idx < len(module_data):
                    try:
                        # new_parts 可能是字符串或数字
                        module_data[idx]["parts"] = int(new_parts) if new_parts else 1
                    except (ValueError, TypeError):
                        pass
            
            def add_module_row(m_name=None, m_parts=1):
                """添加一个Module输入行"""
                if m_name is None:
                    m_name = f"Module {len(module_data) + 1}"
                module_data.append({"name": m_name, "parts": m_parts})
                _render_module_row(len(module_data) - 1, m_name, m_parts)

            def _render_module_row(idx: int, name: str, parts: int):
                with modules_container:
                    with ui.row().classes("gap-2 items-center"):
                        name_inp = ui.input("Module名称", value=name).classes("flex-1")
                        name_inp.on("change", lambda e, i=idx: _update_module_name(i, e.args))

                        parts_inp = ui.number("Part数", value=parts, min=1).classes("w-20")
                        parts_inp.on("change", lambda e, i=idx: _update_module_parts(i, e.args))

                        ui.button("", on_click=lambda i=idx: remove_module(i), icon="delete") \
                            .props("size=sm flat color=red")

            def remove_module(idx: int):
                """删除指定Module"""
                if 0 <= idx < len(module_data):
                    module_data.pop(idx)
                _rebuild_module_rows()

            def _rebuild_module_rows():
                """重建Module行"""
                modules_container.clear()
                for i, m in enumerate(module_data):
                    _render_module_row(i, m["name"], m["parts"])

            # 显示/隐藏配置区 - 切换时重建内容
            def on_progress_type_change():
                pt_label = progress_type_select.value
                pt_value = _progress_type_label_to_value(pt_label)

                linear_config.clear()
                hierarchical_config.clear()

                if pt_value == PROGRESS_LINEAR:
                    with linear_config:
                        nonlocal total_units_input, unit_label_input
                        total_units_input = ui.number(
                            "总单位数",
                            value=(project.total_units if project else 0) or 0,
                            min=0
                        ).classes("w-32")
                        unit_label_input = ui.input(
                            "单位标签",
                            value=(project.unit_label if project else None) or "页"
                        ).classes("w-32")

                elif pt_value == PROGRESS_HIERARCHICAL:
                    with hierarchical_config:
                        nonlocal modules_container
                        modules_container = ui.column().classes("w-full gap-2")
                        if module_data:
                            _rebuild_module_rows()
                        ui.button("+ 添加Module", on_click=lambda: add_module_row()).props("size=sm")

            progress_type_select.on("change", on_progress_type_change)
            ui.timer(0.05, lambda: on_progress_type_change(), once=True)

            # 其他信息
            ui.separator()
            ui.label("其他信息").classes("font-bold")

            with ui.row().classes("gap-4 w-full"):
                with ui.column().classes("flex-1"):
                    ui.label("起始日期").classes("text-xs font-bold mb-1")
                    ui.label("项目实际开始的日期，可早于今天").classes("text-xs text-gray-400 mb-2")
                    start_date_input = ui.date(
                        value=str(project.last_active_date) if project and project.last_active_date else str(date.today())
                    )

                with ui.column().classes("flex-1"):
                    ui.label("预期完成日期").classes("text-xs font-bold mb-1")
                    ui.label("设定目标完成时间，用于追踪进度").classes("text-xs text-gray-400 mb-2")
                    end_date_input = ui.date(
                        value=str(project.expected_end_date) if project and project.expected_end_date else None
                    )

            with ui.row().classes("gap-4 w-full mt-4"):
                priority_select = ui.select(
                    options=[PRIORITY_LABELS[p] for p in PRIORITY_OPTIONS],
                    label="优先级",
                    value=PRIORITY_LABELS.get(project.priority, "中") if project else "中"
                ).classes("flex-1")

            # 标签
            existing_tags = get_all_tags()
            tags_value = ",".join(project.tags) if project else ""
            tags_input = ui.input(
                "标签(逗号分隔)",
                value=tags_value,
                placeholder="如: 计算机,基础,必读"
            ).classes("w-full")
            if existing_tags:
                ui.label(f"已有标签: {', '.join(existing_tags)}").classes("text-xs text-gray-400")

            # 状态（编辑时可改）
            if is_edit:
                status_select = ui.select(
                    options=[STATUS_LABELS[s] for s in [STATUS_BACKLOG, STATUS_IN_PROGRESS, STATUS_PAUSED, STATUS_DONE, STATUS_ARCHIVED]],
                    label="状态",
                    value=STATUS_LABELS.get(project.status, "规划中")
                ).classes("w-full")

            # 按钮
            with ui.row().classes("gap-2 justify-end mt-4"):
                ui.button("取消", on_click=dialog.close)

                def save():
                    # 验证
                    if not name_input.value:
                        ui.notify("请输入项目名称", type="warning")
                        return

                    # 构造Project对象
                    pt_label = progress_type_select.value
                    pt_value = _progress_type_label_to_value(pt_label)

                    modules = []
                    if pt_value == PROGRESS_HIERARCHICAL:
                        modules = [ModuleInfo(name=m["name"], total_parts=m["parts"]) for m in module_data]

                    new_project = Project(
                        id=project.id if project else None,
                        name=name_input.value,
                        type=_type_label_to_value(type_select.value) or "book",
                        source=_source_label_to_value(source_select.value) or "other",
                        url=url_input.value or "",
                        progress_type=pt_value,
                        total_units=int(total_units_input.value) if pt_value == PROGRESS_LINEAR and total_units_input else None,
                        unit_label=(unit_label_input.value if unit_label_input else None) or "页",
                        modules=modules,
                        expected_end_date=date.fromisoformat(end_date_input.value) if end_date_input.value else None,
                        priority=_priority_label_to_value(priority_select.value) or "medium",
                        tags=[t.strip() for t in (tags_input.value or "").split(",") if t.strip()],
                        status=_status_label_to_value(status_select.value) if is_edit and status_select.value else (project.status if project else STATUS_BACKLOG),
                        total_progress=project.total_progress if project else 0,
                        last_active_date=date.fromisoformat(start_date_input.value) if start_date_input.value else None,
                    )

                    if is_edit:
                        project_service.update(new_project)
                        ui.notify("项目已更新", type="positive")
                    else:
                        project_service.create(new_project)
                        ui.notify("项目已创建", type="positive")

                    dialog.close()
                    refresh_list()

                ui.button("保存", on_click=save, icon="save").classes("bg-blue-500 text-white")

        dialog.open()

    # ─── 顶部工具栏（open_create_dialog 已在上方定义，不会再报错）───

    with ui.row().classes("items-center gap-4 p-4 flex-wrap"):
        search_input = ui.input(placeholder="搜索项目名称...").classes("w-48")

        type_filter = ui.select(
            options=["全部"] + [TYPE_LABELS[t] for t in TYPE_OPTIONS],
            label="类型",
            value="全部"
        ).classes("w-24")

        status_filter = ui.select(
            options=["全部"] + [STATUS_LABELS[s] for s in STATUS_OPTIONS],
            label="状态",
            value="全部"
        ).classes("w-24")

        ui.button("搜索", on_click=lambda: refresh_list(), icon="search")

        ui.space()
        ui.button("+ 新建项目", on_click=open_create_dialog, icon="add").classes("bg-blue-500 text-white")

    # 初始加载
    refresh_list()