"""
插件基类和接口。

本模块定义了所有插件必须实现的抽象基类和数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class Severity(Enum):
    """严重程度枚举。"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class SectionType(Enum):
    """展示区块类型枚举。"""
    STATS = "stats"
    TABLE = "table"
    TIMELINE = "timeline"
    CARDS = "cards"
    CHART = "chart"
    SEARCH_BOX = "search_box"
    RAW = "raw"


# ========== Meta 元数据 ==========

@dataclass
class ResultMeta:
    """插件结果元数据。"""
    plugin_id: str
    plugin_name: str
    version: str
    analysis_time: str
    log_file: str
    plugin_type: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            'plugin_id': self.plugin_id,
            'plugin_name': self.plugin_name,
            'version': self.version,
            'analysis_time': self.analysis_time,
            'log_file': self.log_file,
            'plugin_type': self.plugin_type,
            'description': self.description
        }


# ========== Section 数据类 ==========

@dataclass
class StatsItem:
    """统计项。"""
    label: str
    value: Any
    unit: str = ""
    severity: str = "info"
    icon: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'label': self.label,
            'value': self.value,
            'unit': self.unit,
            'severity': self.severity,
            'icon': self.icon
        }


@dataclass
class StatsSection:
    """统计概览区块。"""
    title: str = ""
    icon: str = "chart-bar"
    items: List[StatsItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'stats',
            'title': self.title,
            'icon': self.icon,
            'items': [item.to_dict() for item in self.items]
        }


@dataclass
class TableColumn:
    """表格列定义。"""
    key: str
    label: str
    type: str = "text"
    width: str = ""
    truncate: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'label': self.label,
            'type': self.type,
            'width': self.width,
            'truncate': self.truncate
        }


@dataclass
class TableSection:
    """表格区块。"""
    title: str = ""
    severity: str = "info"
    icon: str = "table"
    columns: List[Dict] = field(default_factory=list)
    rows: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'table',
            'title': self.title,
            'severity': self.severity,
            'icon': self.icon,
            'columns': self.columns,
            'rows': self.rows
        }


@dataclass
class TimelineEvent:
    """时间线事件。"""
    timestamp: str
    title: str
    description: str = ""
    severity: str = "info"
    icon: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'icon': self.icon,
            'detail': self.detail
        }


@dataclass
class TimelineSection:
    """时间线区块。"""
    title: str = ""
    icon: str = "clock"
    events: List[TimelineEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'timeline',
            'title': self.title,
            'icon': self.icon,
            'events': [e.to_dict() for e in self.events]
        }


@dataclass
class CardItem:
    """卡片项。"""
    title: str
    severity: str = "info"
    icon: str = ""
    content: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'severity': self.severity,
            'icon': self.icon,
            'content': self.content
        }


@dataclass
class CardsSection:
    """卡片区块。"""
    title: str = ""
    icon: str = "layers"
    cards: List[CardItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'cards',
            'title': self.title,
            'icon': self.icon,
            'cards': [c.to_dict() for c in self.cards]
        }


@dataclass
class ChartData:
    """图表数据。"""
    labels: List[str] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'labels': self.labels,
            'values': self.values
        }


@dataclass
class ChartSection:
    """图表区块。"""
    title: str = ""
    icon: str = "chart-bar"
    chart_type: str = "bar"
    data: ChartData = field(default_factory=ChartData)
    options: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'chart',
            'title': self.title,
            'icon': self.icon,
            'chart_type': self.chart_type,
            'data': self.data.to_dict(),
            'options': self.options
        }


@dataclass
class SearchBoxSection:
    """搜索框区块。"""
    title: str = ""
    icon: str = "search"
    placeholder: str = ""
    data: List[Dict] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'search_box',
            'title': self.title,
            'icon': self.icon,
            'placeholder': self.placeholder,
            'data': self.data,
            'search_fields': self.search_fields
        }


@dataclass
class RawSection:
    """原始数据区块。"""
    title: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'raw',
            'title': self.title,
            'data': self.data
        }


# ========== AnalysisResult ==========

@dataclass
class AnalysisResult:
    """插件分析结果。"""
    meta: ResultMeta
    sections: List[Any] = field(default_factory=list)

    def add_stats(self, title: str, items: List[StatsItem], icon: str = "chart-bar"):
        """添加统计概览区块。"""
        self.sections.append(StatsSection(title=title, icon=icon, items=items))

    def add_table(self, title: str, columns: List[Dict], rows: List[Dict],
                  severity: str = "info", icon: str = "table"):
        """添加表格区块。"""
        self.sections.append(TableSection(
            title=title, severity=severity, icon=icon, columns=columns, rows=rows
        ))

    def add_timeline(self, title: str, events: List[TimelineEvent], icon: str = "clock"):
        """添加时间线区块。"""
        self.sections.append(TimelineSection(title=title, icon=icon, events=events))

    def add_cards(self, title: str, cards: List[CardItem], icon: str = "layers"):
        """添加卡片区块。"""
        self.sections.append(CardsSection(title=title, icon=icon, cards=cards))

    def add_chart(self, title: str, chart_type: str, data: ChartData,
                  options: Dict[str, str] = None, icon: str = "chart-bar"):
        """添加图表区块。"""
        self.sections.append(ChartSection(
            title=title, icon=icon, chart_type=chart_type, data=data,
            options=options or {}
        ))

    def add_search_box(self, title: str, data: List[Dict], search_fields: List[str],
                       placeholder: str = "", icon: str = "search"):
        """添加搜索框区块。"""
        self.sections.append(SearchBoxSection(
            title=title, icon=icon, placeholder=placeholder,
            data=data, search_fields=search_fields
        ))

    def add_raw(self, title: str, data: Dict[str, Any]):
        """添加原始数据区块。"""
        self.sections.append(RawSection(title=title, data=data))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便 JSON 序列化。"""
        return {
            'meta': self.meta.to_dict(),
            'sections': [s.to_dict() for s in self.sections]
        }


# ========== BasePlugin ==========

class BasePlugin(ABC):
    """
    所有插件的抽象基类。

    插件元数据通过 plugin.json 配置，由 PluginManager 加载时读取并注入。
    """

    def __init__(self):
        self._log_callback: Optional[Callable[[str], None]] = None
        self._id: str = ""
        self._name: str = ""
        self._plugin_type: str = ""
        self._version: str = "1.0.0"
        self._description: str = ""

    @property
    def id(self) -> str:
        """插件唯一标识符。"""
        return self._id

    @property
    def name(self) -> str:
        """插件名称。"""
        return self._name

    def get_plugin_type(self) -> str:
        """插件所属类型：CloudBMC、iBMC、LxBMC。"""
        return self._plugin_type

    def get_chinese_description(self) -> str:
        """中文描述。"""
        return self._description

    def get_version(self) -> str:
        """版本号。"""
        return self._version

    def set_metadata(self, id: str = None, name: str = None,
                     plugin_type: str = None, version: str = None,
                     description: str = None) -> None:
        """设置插件元数据（由 PluginManager 调用）。"""
        if id is not None:
            self._id = id
        if name is not None:
            self._name = name
        if plugin_type is not None:
            self._plugin_type = plugin_type
        if version is not None:
            self._version = version
        if description is not None:
            self._description = description

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """设置日志记录回调函数。"""
        self._log_callback = callback

    def log(self, message: str) -> None:
        """使用回调函数记录日志。"""
        if self._log_callback:
            self._log_callback(f"[{self.name}] {message}")

    @abstractmethod
    def analyze(self, log_file: str) -> AnalysisResult:
        """
        分析日志文件。

        Args:
            log_file: 要分析的日志文件路径。

        Returns:
            包含分析结果的 AnalysisResult。
        """
        pass