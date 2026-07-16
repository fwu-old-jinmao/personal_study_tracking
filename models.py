"""数据模型定义"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date


@dataclass
class ModuleInfo:
    """层级型项目的Module结构"""
    name: str
    total_parts: int


@dataclass
class Project:
    """项目模型"""
    id: Optional[int] = None
    name: str = ""
    type: str = "book"
    source: str = "other"
    url: str = ""
    progress_type: str = "linear"
    total_units: Optional[int] = None
    unit_label: str = "页"
    modules: List[ModuleInfo] = field(default_factory=list)
    expected_end_date: Optional[date] = None
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    status: str = "backlog"
    total_progress: float = 0.0
    last_active_date: Optional[date] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProgressRecord:
    """进度记录模型"""
    id: Optional[int] = None
    project_id: int = 0
    record_date: date = field(default_factory=date.today)
    # 线性型字段
    start_value: Optional[int] = None
    end_value: Optional[int] = None
    # 层级型字段
    module_index: Optional[int] = None
    module_name: Optional[str] = None
    part_start: Optional[int] = None
    part_end: Optional[int] = None
    total_parts: Optional[int] = None
    # 通用
    progress_note: str = ""
    created_at: Optional[str] = None


@dataclass
class Note:
    """笔记模型"""
    id: Optional[int] = None
    project_id: int = 0
    title: str = ""
    content: str = ""
    chapter_tag: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None