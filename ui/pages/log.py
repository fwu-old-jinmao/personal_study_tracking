"""每日进度录入页面"""
from datetime import date, timedelta
from nicegui import ui
from services.project_service import ProjectService
from services.progress_service import ProgressService
from models import ProgressRecord
from config import (
    PROGRESS_LINEAR, PROGRESS_HIERARCHICAL, PROGRESS_PERCENTAGE,
    PROGRESS_TYPE_LABELS, TYPE_LABELS,
)

project_service = ProjectService()
progress_service = ProgressService()


@ui.page("/log")
def log_page():
    """每日进度录入页面"""
    ui.label("✏️ 每日进度录入").classes("text-2xl font-bold p-4")

    # ─── 日期选择 ───
    with ui.row().classes("items-center gap-3 p-4 flex-wrap"):
        ui.label("选择日期：").classes("text-sm")
        log_date = ui.date(value=date.today().isoformat()).classes("w-36")

        with ui.row().classes("gap-2"):
            ui.button("今天", on_click=lambda: log_date.set_value(date.today().isoformat())) \
                .props("size=sm flat")
            ui.button("昨天", on_click=lambda: log_date.set_value((date.today() - timedelta(days=1)).isoformat())) \
                .props("size=sm flat")
            ui.button("前天", on_click=lambda: log_date.set_value((date.today() - timedelta(days=2)).isoformat())) \
                .props("size=sm flat")

    # ─── 左右分栏 ───
    with ui.row().classes("w-full gap-4 p-4"):
        # 左侧：项目选择 + 录入表单
        with ui.column().classes("flex-1"):
            _build_input_area(log_date)

        # 右侧：今日已录入列表
        with ui.column().classes("w-80"):
            _build_today_records(log_date)


def _build_input_area(log_date):
    """构建左侧录入区域"""
    active_projects = project_service.get_by_status_list(["in_progress", "backlog", "paused"])

    project_options = {}
    for p in active_projects:
        icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(p.type, "📌")
        label = f"{icon} {p.name}"
        project_options[label] = p

    ui.label("选择项目").classes("font-bold mb-2")
    # project_select = ui.select(
    #     options=list(project_options.keys()),
    #     label="项目",
    #     value=None,
    #     with_input=True
    # ).classes("w-full mb-4").props('clearable')
    def on_project_changed(e):
        """项目选择变化时触发"""
        print("DEBUG: on_project_changed called")
        print(f"DEBUG: selected value = {e.value}")
        
        form_card.clear()
        preview_card.clear()

        selected_label = e.value
        if not selected_label or selected_label not in project_options:
            return

        project = project_options[selected_label]

        with form_card:
            ui.label(f"📌 {project.name}").classes("font-bold text-lg")
            ui.label(f"类型：{TYPE_LABELS.get(project.type, '')} | "
                    f"进度类型：{PROGRESS_TYPE_LABELS.get(project.progress_type, '')} | "
                    f"总进度：{project.total_progress}%").classes("text-sm text-gray-500 mb-3")

            if project.progress_type == PROGRESS_LINEAR:
                _build_linear_form(project, preview_card, log_date)
            elif project.progress_type == PROGRESS_HIERARCHICAL:
                _build_hierarchical_form(project, preview_card, log_date)
            elif project.progress_type == PROGRESS_PERCENTAGE:
                _build_percentage_form(project, preview_card, log_date)


    project_select = ui.select(
        options=list(project_options.keys()),
        label="项目",
        value=None,
        with_input=True,
        on_change=on_project_changed  # 直接在创建时绑定
    ).classes("w-full mb-4").props('clearable')

    # 快捷项目标签
    if active_projects:
        ui.label("最近活跃：").classes("text-xs text-gray-500 mt-1")
        with ui.row().classes("gap-2 flex-wrap"):
            sorted_projects = sorted(
                active_projects,
                key=lambda p: str(p.last_active_date or ""),
                reverse=True
            )[:5]
            for p in sorted_projects:
                icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(p.type, "📌")
                btn_label = f"{icon} {p.name[:8]}{'...' if len(p.name) > 8 else ''}"
                ui.button(btn_label, on_click=lambda _, pl=p: _select_project(pl, project_select, project_options)) \
                    .props("size=sm flat dense")

    # 录入表单容器
    form_card = ui.card().classes("w-full mt-4 p-4 bg-gray-50")
    preview_card = ui.card().classes("w-full mt-2")

    def on_project_changed():
        """项目选择变化时，动态构建录入表单"""
        form_card.clear()
        preview_card.clear()

        print("DEBUG: on_project_changed called")  # 加这行
        selected_label = project_select.value
        print(f"DEBUG: selected_label = {selected_label}")  # 加这行
        if not selected_label or selected_label not in project_options:
            return

        project = project_options[selected_label]

        with form_card:
            ui.label(f"📌 {project.name}").classes("font-bold text-lg")
            ui.label(f"类型：{TYPE_LABELS.get(project.type, '')} | "
                     f"进度类型：{PROGRESS_TYPE_LABELS.get(project.progress_type, '')} | "
                     f"总进度：{project.total_progress}%").classes("text-sm text-gray-500 mb-3")

            if project.progress_type == PROGRESS_LINEAR:
                _build_linear_form(project, preview_card, log_date)
            elif project.progress_type == PROGRESS_HIERARCHICAL:
                _build_hierarchical_form(project, preview_card, log_date)
            elif project.progress_type == PROGRESS_PERCENTAGE:
                _build_percentage_form(project, preview_card, log_date)

    # project_select.on("change", on_project_changed)


def _select_project(project, project_select, project_options):
    """从快捷按钮选择项目"""
    for label, p in project_options.items():
        if p.id == project.id:
            project_select.set_value(label)
            break


def _build_progress_form_content(project, preview_container, log_date):
    """在 form_container 上下文中构建表单（拆分出来避免嵌套过深）"""
    ui.label(f"📌 {project.name}").classes("font-bold text-lg")
    ui.label(f"类型：{TYPE_LABELS.get(project.type, '')} | "
             f"进度类型：{PROGRESS_TYPE_LABELS.get(project.progress_type, '')} | "
             f"总进度：{project.total_progress}%").classes("text-sm text-gray-500 mb-3")

    if project.progress_type == PROGRESS_LINEAR:
        _build_linear_form(project, preview_container, log_date)
    elif project.progress_type == PROGRESS_HIERARCHICAL:
        _build_hierarchical_form(project, preview_container, log_date)
    elif project.progress_type == PROGRESS_PERCENTAGE:
        _build_percentage_form(project, preview_container, log_date)

# def _build_progress_form(project, container, preview_container, log_date):
#     """根据项目类型构建录入表单"""
#     with container:
#         ui.label(f"📌 {project.name}").classes("font-bold text-lg")
#         ui.label(f"类型：{TYPE_LABELS.get(project.type, '')} | "
#                  f"进度类型：{PROGRESS_TYPE_LABELS.get(project.progress_type, '')} | "
#                  f"总进度：{project.total_progress}%").classes("text-sm text-gray-500 mb-3")

#         if project.progress_type == PROGRESS_LINEAR:
#             _build_linear_form(project, container, preview_container, log_date)
#         elif project.progress_type == PROGRESS_HIERARCHICAL:
#             _build_hierarchical_form(project, container, preview_container, log_date)
#         elif project.progress_type == PROGRESS_PERCENTAGE:
#             _build_percentage_form(project, container, preview_container, log_date)


# def _build_linear_form(project, container, preview_container, log_date):
def _build_linear_form(project, preview_container, log_date):
    """线性型录入表单"""
    total = project.total_units or 1
    unit = project.unit_label or "页"

    # 获取上次结束值
    last_end = progress_service.get_last_progress(project.id)
    default_start = (last_end or 0) + 1 if last_end else 1

    # 输入区
    start_input = ui.number(
        f"起始{unit}",
        value=default_start,
        min=1,
        max=total
    ).classes("w-32")

    end_input = ui.number(
        f"截止{unit}",
        value=default_start,
        min=1,
        max=total
    ).classes("w-32")

    note_input = ui.textarea(
        "备注（可选）",
        placeholder="一两句感想..."
    ).classes("w-full max-w-md")

    # 实时预览
    def update_preview():
        preview_container.clear()
        start = int(start_input.value) if start_input.value else 0
        end = int(end_input.value) if end_input.value else 0
        if start > end:
            with preview_container:
                ui.label("⚠️ 起始值不能大于截止值").classes("text-red-500 text-sm")
            return
        pages_read = end - start + 1
        new_total = max(end, (last_end or 0))
        new_percent = min(round(new_total / total * 100, 1), 100)

        with preview_container:
            ui.label(f"本次阅读：P{start}-{end}/{total}{unit}（共{pages_read}{unit}）").classes("text-sm font-bold")
            ui.label(f"累计进度：{new_percent}%").classes("text-sm text-blue-600")
            ui.linear_progress(value=new_percent / 100).classes("w-full")

    start_input.on("change", update_preview)
    end_input.on("change", update_preview)
    update_preview()

    # 保存按钮
    def save_linear():
        start = int(start_input.value) if start_input.value else 0
        end = int(end_input.value) if end_input.value else 0
        if start <= 0 or end <= 0:
            ui.notify("请输入有效的起始和截止值", type="warning")
            return
        if start > end:
            ui.notify("起始值不能大于截止值", type="warning")
            return

        try:
            record_date = date.fromisoformat(log_date.value)
        except (ValueError, TypeError):
            ui.notify("请选择有效日期", type="warning")
            return

        record = ProgressRecord(
            project_id=project.id,
            record_date=record_date,
            start_value=start,
            end_value=end,
            progress_note=note_input.value or "",
        )
        progress_service.create(record)
        ui.notify(f"✅ {project.name}：P{start}-{end}/{total}{unit}", type="positive")

        # 重置表单
        start_input.set_value(end + 1)
        end_input.set_value(end + 1)
        note_input.set_value("")
        update_preview()

    preview_container.clear()
    ui.button("保存录入", on_click=save_linear, icon="save") \
        .classes("mt-3 bg-green-500 text-white")


def _build_hierarchical_form(project, preview_container, log_date):
    """层级型录入表单"""
    if not project.modules:
        ui.label("⚠️ 该项目未配置Module结构，请先编辑项目添加Module").classes("text-red-500")
        return

    module_names = [f"M{i+1}：{m.name} ({m.total_parts}个Part)" for i, m in enumerate(project.modules)]

    module_select = ui.select(
        options=module_names,
        label="选择Module",
        value=module_names[0] if module_names else None
    ).classes("w-full max-w-md")

    # Part输入
    part_start_input = ui.number("起始Part", value=1, min=1).classes("w-28")
    part_end_input = ui.number("截止Part", value=1, min=1).classes("w-28")
    total_parts_display = ui.label("").classes("text-sm text-gray-500")

    note_input = ui.textarea(
        "备注（可选）",
        placeholder="一两句感想..."
    ).classes("w-full max-w-md")

    def on_module_change():
        """切换Module时更新Part范围和总数"""
        selected = module_select.value
        if not selected or not module_names:
            return
        idx = module_names.index(selected)
        m = project.modules[idx]
        total_parts_display.set_text(f"该Module共 {m.total_parts} 个Part")

        # 设置Part输入的最大值
        part_start_input.props(f"max={m.total_parts}")
        part_end_input.props(f"max={m.total_parts}")

        # 自动填充上次进度
        last_part = progress_service.get_last_module_progress(project.id, idx)
        default_part = (last_part or 0) + 1 if last_part else 1
        if default_part > m.total_parts:
            default_part = m.total_parts
        part_start_input.set_value(default_part)
        part_end_input.set_value(default_part)

        update_preview()

    module_select.on("change", on_module_change)

    def update_preview():
        preview_container.clear()
        selected = module_select.value
        if not selected or selected not in module_names:
            return
        idx = module_names.index(selected)
        m = project.modules[idx]

        p_start = int(part_start_input.value) if part_start_input.value else 0
        p_end = int(part_end_input.value) if part_end_input.value else 0

        if p_start > p_end:
            with preview_container:
                ui.label("⚠️ 起始Part不能大于截止Part").classes("text-red-500 text-sm")
            return

        # 计算总进度
        total_parts_all = sum(m.total_parts for m in project.modules)
        completed = 0
        for i, mod in enumerate(project.modules):
            if i < idx:
                completed += mod.total_parts
            elif i == idx:
                completed += p_end
        new_percent = min(round(completed / total_parts_all * 100, 1), 100)

        with preview_container:
            ui.label(f"本次学习：{m.name} — Part {p_start}-{p_end}/{m.total_parts}").classes("text-sm font-bold")
            ui.label(f"累计进度：{new_percent}%").classes("text-sm text-blue-600")
            ui.linear_progress(value=new_percent / 100).classes("w-full")

    def save_hierarchical():
        selected = module_select.value
        if not selected or selected not in module_names:
            return
        idx = module_names.index(selected)
        m = project.modules[idx]

        p_start = int(part_start_input.value) if part_start_input.value else 0
        p_end = int(part_end_input.value) if part_end_input.value else 0
        if p_start <= 0 or p_end <= 0:
            ui.notify("请输入有效的Part范围", type="warning")
            return
        if p_start > p_end:
            ui.notify("起始Part不能大于截止Part", type="warning")
            return

        try:
            record_date = date.fromisoformat(log_date.value)
        except (ValueError, TypeError):
            ui.notify("请选择有效日期", type="warning")
            return

        record = ProgressRecord(
            project_id=project.id,
            record_date=record_date,
            module_index=idx,
            module_name=m.name,
            part_start=p_start,
            part_end=p_end,
            total_parts=m.total_parts,
            progress_note=note_input.value or "",
        )
        progress_service.create(record)
        ui.notify(f"✅ {project.name} — {m.name} Part {p_start}-{p_end}", type="positive")

        # 如果该Module已完成，自动跳到下一个Module
        if p_end >= m.total_parts and idx + 1 < len(project.modules):
            module_select.set_value(module_names[idx + 1])
        else:
            part_start_input.set_value(p_end + 1)
            part_end_input.set_value(p_end + 1)
        note_input.set_value("")
        update_preview()

    preview_container.clear()
    ui.button("保存录入", on_click=save_hierarchical, icon="save") \
        .classes("mt-3 bg-green-500 text-white")

    # 初始化
    on_module_change()


def _build_percentage_form(project, preview_container, log_date):
    """百分比型录入表单"""
    current_pct = project.total_progress

    # 滑块 + 数字输入
    with ui.row().classes("items-center gap-4"):
        pct_slider = ui.slider(min=0, max=100, value=current_pct, step=1).classes("w-48")
        pct_label = ui.label(f"{int(current_pct)}%").classes("text-lg font-bold w-16")

    def on_slider_change():
        pct_label.set_text(f"{int(pct_slider.value)}%")
        update_preview()

    pct_slider.on("change", on_slider_change)

    note_input = ui.textarea(
        "备注（可选）",
        placeholder="一两句感想..."
    ).classes("w-full max-w-md mt-3")

    def update_preview():
        preview_container.clear()
        new_pct = int(pct_slider.value)
        delta = new_pct - current_pct
        with preview_container:
            if delta > 0:
                ui.label(f"本次推进：+{delta}%").classes("text-sm font-bold text-green-600")
            elif delta < 0:
                ui.label(f"⚠️ 进度回退：{delta}%").classes("text-sm text-orange-500")
            else:
                ui.label("进度无变化").classes("text-sm text-gray-500")
            ui.label(f"更新后进度：{new_pct}%").classes("text-sm text-blue-600")
            ui.linear_progress(value=new_pct / 100).classes("w-full")

    update_preview()

    def save_percentage():
        new_pct = int(pct_slider.value)
        try:
            record_date = date.fromisoformat(log_date.value)
        except (ValueError, TypeError):
            ui.notify("请选择有效日期", type="warning")
            return

        record = ProgressRecord(
            project_id=project.id,
            record_date=record_date,
            end_value=new_pct,
            progress_note=note_input.value or "",
        )
        progress_service.create(record)
        ui.notify(f"✅ {project.name}：{new_pct}%", type="positive")
        note_input.set_value("")

    preview_container.clear()
    ui.button("保存录入", on_click=save_percentage, icon="save") \
        .classes("mt-3 bg-green-500 text-white")


def _build_today_records(log_date):
    """构建右侧今日录入列表"""
    ui.label("📋 今日录入").classes("font-bold mb-3")

    records_container = ui.column().classes("w-full gap-2")
    stats_label = ui.label("").classes("text-xs text-gray-500 mt-2")

    def refresh_records():
        records_container.clear()
        try:
            d = date.fromisoformat(log_date.value)
        except (ValueError, TypeError):
            return

        records = progress_service.get_by_date(d)

        # 统计
        total_projects = len(set(r.project_id for r in records))
        total_pages = sum(
            (r.end_value - r.start_value + 1)
            for r in records
            if r.start_value and r.end_value
        )
        stats_label.set_text(f"共 {total_projects} 个项目 | 阅读/学习量：{total_pages}")

        with records_container:
            if not records:
                ui.label("暂无录入").classes("text-gray-400 text-sm p-4 text-center w-full")
            for r in records:
                proj = project_service.get_by_id(r.project_id)
                proj_name = proj.name if proj else f"项目#{r.project_id}"
                icon = {"book": "📖", "course": "🎓", "other": "📌"}.get(proj.type, "📌") if proj else "📌"

                with ui.card().classes("w-full p-2"):
                    with ui.row().classes("items-center justify-between"):
                        ui.label(f"{icon} {proj_name}").classes("font-medium text-sm flex-1")

                    # 进度描述
                    if r.start_value and r.end_value:
                        total = proj.total_units if proj else "?"
                        unit = proj.unit_label if proj else "页"
                        ui.label(f"P{r.start_value}-{r.end_value}/{total}{unit}").classes("text-xs text-gray-500")
                    elif r.module_name:
                        ui.label(f"{r.module_name} Part {r.part_start}-{r.part_end}/{r.total_parts}").classes("text-xs text-gray-500")
                    else:
                        ui.label(f"进度：{r.end_value}%").classes("text-xs text-gray-500")

                    if r.progress_note:
                        ui.label(f"💬 {r.progress_note[:50]}{'...' if len(r.progress_note) > 50 else ''}") \
                            .classes("text-xs text-gray-400 mt-1")

                    with ui.row().classes("gap-1 justify-end"):
                        ui.button("", on_click=lambda rid=r.id: _delete_record(rid, log_date, refresh_records), icon="delete") \
                            .props("size=xs flat color=red dense")

    def _delete_record(record_id, log_date, refresh_fn):
        progress_service.delete(record_id)
        ui.notify("已删除", type="warning")
        refresh_fn()

    # 监听日期变化刷新
    log_date.on("change", refresh_records)

    # 初始加载
    refresh_records()

    # 返回刷新函数供外部调用
    return refresh_records