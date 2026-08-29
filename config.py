"""应用配置文件"""
import os

# 数据库路径：优先从环境变量读取，本地开发用默认路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# DB_PATH = os.path.join(DATA_DIR, "tracker.db")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "tracker.db"
))

# 确保数据目录存在
# os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 项目状态定义
STATUS_BACKLOG = "backlog"       # 规划中
STATUS_IN_PROGRESS = "in_progress"  # 进行中
STATUS_PAUSED = "paused"        # 暂缓
STATUS_DONE = "done"            # 已完成
STATUS_ARCHIVED = "archived"    # 已归档

STATUS_OPTIONS = [
    STATUS_BACKLOG,
    STATUS_IN_PROGRESS,
    STATUS_PAUSED,
    STATUS_DONE,
    STATUS_ARCHIVED,
]

STATUS_LABELS = {
    STATUS_BACKLOG: "规划中",
    STATUS_IN_PROGRESS: "进行中",
    STATUS_PAUSED: "暂缓",
    STATUS_DONE: "已完成",
    STATUS_ARCHIVED: "已归档",
}

# 项目类型
TYPE_BOOK = "book"
TYPE_COURSE = "course"
TYPE_OTHER = "other"

TYPE_OPTIONS = [TYPE_BOOK, TYPE_COURSE, TYPE_OTHER]
TYPE_LABELS = {TYPE_BOOK: "书籍", TYPE_COURSE: "课程", TYPE_OTHER: "其他"}

# 进度类型
PROGRESS_LINEAR = "linear"
PROGRESS_HIERARCHICAL = "hierarchical"
PROGRESS_PERCENTAGE = "percentage"

PROGRESS_TYPE_OPTIONS = [PROGRESS_LINEAR, PROGRESS_HIERARCHICAL, PROGRESS_PERCENTAGE]
PROGRESS_TYPE_LABELS = {
    PROGRESS_LINEAR: "线性型 (页数/集数)",
    PROGRESS_HIERARCHICAL: "层级型 (Module/Part)",
    PROGRESS_PERCENTAGE: "百分比型",
}

# 来源选项
SOURCE_OPTIONS = ["coursera", "dedao", "bilibili", "other"]
SOURCE_LABELS = {
    "coursera": "Coursera",
    "dedao": "得到",
    "bilibili": "B站",
    "other": "其他",
}

# 优先级
PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"

PRIORITY_OPTIONS = [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]
PRIORITY_LABELS = {PRIORITY_HIGH: "高", PRIORITY_MEDIUM: "中", PRIORITY_LOW: "低"}

# 看板中Done列保留天数
DONE_RETENTION_DAYS = 7