"""
Personal Learning Tracker - M1 & M2
项目管理 + Kanban看板
"""
from nicegui import ui
from database import init_db
from ui.pages.log import log_page


@ui.page("/")
def index():
    """首页重定向到看板"""
    ui.navigate.to("/kanban")


# ─── 导入页面路由 ───
from ui.pages.projects import projects_page
from ui.pages.kanban import kanban_page


def render_nav():
    """渲染导航栏"""
    with ui.row().classes("items-center gap-4 w-full px-4 py-2"):
        ui.label("📊 PLT").classes("text-lg font-bold")
        ui.button("看板", on_click=lambda: ui.navigate.to("/kanban")).props("flat")
        ui.button("项目管理", on_click=lambda: ui.navigate.to("/projects")).props("flat")
        ui.button("录入", on_click=lambda: ui.navigate.to("/log")).props("flat")
        ui.button("完成记录", on_click=lambda: ui.navigate.to("/history")).props("flat")
        ui.button("统计", on_click=lambda: ui.navigate.to("/stats")).props("flat")
        ui.space()


# ─── 全局布局 ───
@ui.page("/kanban")
def kanban_with_nav():
    with ui.header().classes("bg-white text-black shadow-sm"):
        render_nav()
    # 直接调用看板逻辑
    from ui.pages.kanban import kanban_page as _kanban
    _kanban()


@ui.page("/projects")
def projects_with_nav():
    with ui.header().classes("bg-white text-black shadow-sm"):
        render_nav()
    from ui.pages.projects import projects_page as _projects
    _projects()


@ui.page("/log")
def log_with_nav():
    with ui.header().classes("bg-white text-black shadow-sm"):
        render_nav()
    from ui.pages.log import log_page as _log
    _log()

@ui.page("/history")
def history_with_nav():
    with ui.header().classes("bg-white text-black shadow-sm"):
        render_nav()
    with ui.column().classes("w-full"):
        from ui.pages.history import history_page as _history
        _history()

@ui.page("/stats")
def stats_with_nav():
    with ui.header().classes("bg-white text-black shadow-sm"):
        render_nav()
    from ui.pages.stats import stats_page as _stats
    _stats()


# ─── 启动 ───
if __name__ == "__main__":
    print("初始化数据库...")
    init_db()
    print("数据库初始化完成")

    print("启动 Personal Learning Tracker...")
    ui.run(
        title="Personal Learning Tracker",
        port=8080,
        reload=False,
        show=True,
    )