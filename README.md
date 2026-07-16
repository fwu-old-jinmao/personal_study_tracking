# Personal Learning Tracker

个人学习项目追踪系统 — 用于记录和管理读书、在线课程、音频课程等学习项目的进度、状态与完成情况。

## 项目状态

🚧 **开发中** — M1 项目管理模块 + M2 Kanban 看板模块已完成，后续模块逐步上线。

## 已实现功能

### M1 - 项目管理
- 创建项目：支持书籍、课程、其他三种类型
- 编辑项目：修改项目信息、调整进度配置
- 删除项目：含确认对话框，删除后级联清除关联数据
- 项目列表：支持按名称搜索、按类型/状态筛选
- 进度类型支持：
  - **线性型**（书籍页数 / 视频集数）
  - **层级型**（Module / Part 结构）
  - **百分比型**（手动输入百分比）

### M2 - Kanban 看板
- 四列状态管理：规划中 → 进行中 → 暂缓 → 已完成
- 状态流转：通过按钮操作切换项目状态
- 类型筛选：按书籍/课程/其他过滤看板内容
- 已归档区：独立展示已归档项目

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Python 3.x |
| 前端框架 | NiceGUI（底层 Vue 3 + Quasar） |
| 数据库 | SQLite |
| 可视化 | ECharts（预留） |

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/personal-learning-tracker.git
cd personal-learning-tracker

# 2. 安装依赖
pip install nicegui

# 3. 启动应用
python app.py

浏览器自动打开 http://localhost:8080
```

## 项目结构
personal-learning-tracker/
├── app.py                  # 应用入口，页面路由
├── config.py               # 配置文件（状态、类型、标签定义）
├── models.py               # 数据模型（dataclass）
├── database.py             # 数据库初始化与操作
├── services/               # 业务逻辑层（与UI框架解耦）
│   ├── project_service.py  # 项目 CRUD
│   ├── progress_service.py # 进度记录（预留）
│   └── stats_service.py    # 统计分析（预留）
├── ui/                     # UI 层
│   ├── components/         # 可复用组件
│   │   └── project_card.py # 看板卡片
│   └── pages/              # 页面
│       ├── projects.py     # 项目管理页面
│       └── kanban.py       # Kanban 看板页面
└── data/                   # SQLite 数据库文件存放
    └── tracker.db          # 运行后自动生成


## 开发计划
- M1: 项目管理 CRUD

- M2: Kanban 看板

- M3: 每日进度录入

- M4: 完成项目展示（周/月/年视图）

- M5: 可视化统计图表

- M6: 笔记模块

- 响应式适配（手机端）

- 数据导出功能


## 设计原则
- 业务与UI分离：services/ 层纯 Python 逻辑，不依赖任何 UI 框架，为未来迁移到 Vue/React 前端预留空间

- 本地优先：SQLite 本地存储，无需网络，数据安全可控

- 渐进开发：按模块逐步上线，每个模块独立可用


## License
