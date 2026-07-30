"""统计分析页面"""
from datetime import date
from nicegui import ui
from services.stats_service import StatsService

stats_service = StatsService()


@ui.page("/stats")
def stats_page():
    """统计分析页面"""
    ui.label("📊 统计分析").classes("text-2xl font-bold p-4")

    # ─── 汇总卡片 ───
    with ui.row().classes("gap-4 p-4 w-full flex-wrap"):
        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("进行中").classes("text-sm text-gray-500")
            active_count = stats_service.get_active_project_count()
            ui.label(str(active_count)).classes("text-3xl font-bold text-blue-600")

        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("暂缓").classes("text-sm text-gray-500")
            paused_count = stats_service.get_paused_project_count()
            ui.label(str(paused_count)).classes("text-3xl font-bold text-orange-500")

        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("规划中").classes("text-sm text-gray-500")
            backlog_count = stats_service.get_backlog_project_count()
            ui.label(str(backlog_count)).classes("text-3xl font-bold text-gray-500")

        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("本周完成").classes("text-sm text-gray-500")
            weekly_count = stats_service.get_weekly_completed_count()
            ui.label(str(weekly_count)).classes("text-3xl font-bold text-green-600")

        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("本月完成").classes("text-sm text-gray-500")
            monthly_count = stats_service.get_monthly_completed_count()
            ui.label(str(monthly_count)).classes("text-3xl font-bold text-green-600")

        with ui.card().classes("flex-1 min-w-[140px] p-4 text-center"):
            ui.label("连续活跃").classes("text-sm text-gray-500")
            streak = stats_service.get_consecutive_active_days()
            streak_text = f"{streak}天" if streak > 0 else "暂无"
            ui.label(streak_text).classes("text-3xl font-bold text-purple-600")

    # ─── 趋势图 ───
    with ui.card().classes("w-full p-4 mt-4"):
        ui.label("📈 近30天每日推进量").classes("font-bold text-lg mb-4")
        trend_data = stats_service.get_daily_progress_trend(30)
        if trend_data:
            dates = [d["date"][5:] for d in trend_data]  # 只显示 MM-DD
            units = [d["units"] for d in trend_data]
            projects = [d["projects"] for d in trend_data]

            ui.echart({
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["推进量", "项目数"]},
                "xAxis": {"type": "category", "data": dates, "axisLabel": {"rotate": 45, "fontSize": 10}},
                "yAxis": [
                    {"type": "value", "name": "页/Part"},
                    {"type": "value", "name": "项目数"}
                ],
                "series": [
                    {
                        "name": "推进量",
                        "type": "bar",
                        "data": units,
                        "itemStyle": {"color": "#4a90d9"}
                    },
                    {
                        "name": "项目数",
                        "type": "line",
                        "yAxisIndex": 1,
                        "data": projects,
                        "itemStyle": {"color": "#e74c3c"}
                    }
                ],
                "grid": {"bottom": "60px"}
            }).classes("w-full h-80")

    # ─── 类别分布 + 热力图 ───
    with ui.row().classes("w-full gap-4 mt-4"):
        # 类别分布饼图
        with ui.card().classes("flex-1 p-4"):
            ui.label("📊 已完成项目类别分布").classes("font-bold text-lg mb-4")
            cat_data = stats_service.get_category_distribution()
            if cat_data:
                type_labels = {"book": "书籍", "course": "课程", "other": "其他"}
                type_colors = {"book": "#4a90d9", "course": "#7ec8a0", "other": "#e7c86c"}
                chart_data = []
                for d in cat_data:
                    chart_data.append({
                        "name": type_labels.get(d["type"], d["type"]),
                        "value": d["count"],
                        "itemStyle": {"color": type_colors.get(d["type"], "#ccc")}
                    })
                ui.echart({
                    "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                    "series": [{
                        "type": "pie",
                        "radius": ["40%", "70%"],
                        "center": ["50%", "50%"],
                        "data": chart_data,
                        "label": {"show": True, "formatter": "{b}\n{d}%"}
                    }]
                }).classes("w-full h-64")
            else:
                ui.label("暂无完成项目").classes("text-gray-400 p-8 text-center w-full")

        # 年度活跃热力图
        with ui.card().classes("flex-1 p-4"):
            ui.label("🔥 年度活跃热力图").classes("font-bold text-lg mb-4")
            today = date.today()
            heatmap_data = stats_service.get_yearly_heatmap(today.year)
            if heatmap_data:
                # 构建 ECharts 日历热力图数据
                chart_data = [
                    [d["date"], d["value"]]
                    for d in heatmap_data
                ]
                ui.echart({
                    "tooltip": {
                        "trigger": "item",
                        "formatter": "{b}<br/>推进量: {c}"
                    },
                    "visualMap": {
                        "min": 0,
                        "max": max(d["value"] for d in heatmap_data) if heatmap_data else 1,
                        "type": "piecewise",
                        "orient": "horizontal",
                        "left": "center",
                        "bottom": 0,
                        "pieces": [
                            {"min": 0, "max": 0, "color": "#ebedf0", "label": "0"},
                            {"min": 1, "max": 5, "color": "#c6e48b", "label": "1-5"},
                            {"min": 6, "max": 15, "color": "#7ec8a0", "label": "6-15"},
                            {"min": 16, "max": 30, "color": "#4a90d9", "label": "16-30"},
                            {"min": 31, "color": "#1a5276", "label": "30+"},
                        ]
                    },
                    "calendar": {
                        "range": today.year,
                        "cellSize": ["auto", 15],
                        "dayLabel": {"firstDay": 1},
                        "monthLabel": {"show": True}
                    },
                    "series": [{
                        "type": "heatmap",
                        "coordinateSystem": "calendar",
                        "data": chart_data
                    }]
                }).classes("w-full h-64")
            else:
                ui.label("暂无数据").classes("text-gray-400 p-8 text-center w-full")