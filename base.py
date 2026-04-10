"""
插件基类和接口。

本模块定义了所有插件必须实现的抽象基类和数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class PluginCategory(Enum):
    """插件类别枚举。"""
    PARSER = "parser"           # 日志解析插件
    ANALYZER = "analyzer"       # 日志分析插件
    DETECTOR = "detector"       # 问题检测插件
    REPORTER = "reporter"       # 报告生成插件
    OTHER = "other"             # 其他插件


@dataclass
class PluginInfo:
    """插件信息元数据。"""
    id: str
    name: str
    version: str
    description: str
    category: PluginCategory = PluginCategory.OTHER
    author: str = ""
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    target_keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便 JSON 序列化。"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'category': self.category.value,
            'author': self.author,
            'enabled': self.enabled,
            'tags': self.tags,
            'capabilities': self.capabilities,
            'target_keywords': self.target_keywords
        }


@dataclass
class AnalysisResult:
    """插件分析结果。"""
    plugin_id: str
    plugin_name: str
    analysis_time: str
    log_file: str
    error_count: int = 0
    warning_count: int = 0
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    raw_output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便 JSON 序列化。"""
        return {
            'plugin_id': self.plugin_id,
            'plugin_name': self.plugin_name,
            'analysis_time': self.analysis_time,
            'log_file': self.log_file,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'errors': self.errors,
            'warnings': self.warnings,
            'statistics': self.statistics,
            'raw_output': self.raw_output
        }


@dataclass
class MultiPluginAnalysisResult:
    """多插件分析结果，包含每个插件的结构。"""
    analysis_time: str
    log_file: str
    plugins: Dict[str, AnalysisResult] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典以便 JSON 序列化。"""
        return {
            'analysis_time': self.analysis_time,
            'log_file': self.log_file,
            'plugins': {
                plugin_id: result.to_dict()
                for plugin_id, result in self.plugins.items()
            }
        }

    def get_total_errors(self) -> int:
        """获取所有插件的错误总数。"""
        return sum(r.error_count for r in self.plugins.values())

    def get_total_warnings(self) -> int:
        """获取所有插件的警告总数。"""
        return sum(r.warning_count for r in self.plugins.values())

    def get_all_errors(self) -> List[Dict]:
        """获取所有插件的错误信息。"""
        all_errors = []
        for result in self.plugins.values():
            all_errors.extend(result.errors)
        return all_errors

    def get_all_warnings(self) -> List[Dict]:
        """获取所有插件的警告信息。"""
        all_warnings = []
        for result in self.plugins.values():
            all_warnings.extend(result.warnings)
        return all_warnings

    def get_merged_statistics(self) -> Dict[str, Any]:
        """获取所有插件的合并统计数据。"""
        merged = {}
        for result in self.plugins.values():
            for key, value in result.statistics.items():
                if key in merged:
                    if isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                        merged[key] += value
                    elif isinstance(value, dict) and isinstance(merged[key], dict):
                        merged[key].update(value)
                else:
                    merged[key] = value
        return merged


class BasePlugin(ABC):
    """
    所有插件的抽象基类。

    所有插件必须继承此类并实现必需的抽象方法和属性。
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """插件唯一标识符。"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """插件可读名称。"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本字符串。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述。"""
        pass

    @property
    @abstractmethod
    def category(self) -> PluginCategory:
        """插件类别。"""
        pass

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

    # 带默认实现的可选方法

    @property
    def author(self) -> str:
        """插件作者。"""
        return ""

    @property
    def tags(self) -> List[str]:
        """插件标签，用于筛选/搜索。"""
        return []

    @property
    def capabilities(self) -> List[str]:
        """插件能力，用于 AI 选择。"""
        return []

    @property
    def target_keywords(self) -> List[str]:
        """目标关键词，用于 AI 选择。"""
        return []

    def get_ai_description(self) -> str:
        """
        生成 AI 可读的插件描述。

        Returns:
            str: AI 可读的描述文本
        """
        desc = f"插件ID: {self.id}\n"
        desc += f"名称: {self.name}\n"
        desc += f"类别: {self.category.value}\n"
        desc += f"描述: {self.description}\n"
        if self.capabilities:
            desc += f"能力: {', '.join(self.capabilities)}\n"
        if self.target_keywords:
            desc += f"目标关键词: {', '.join(self.target_keywords)}\n"
        return desc

    def validate_config(self) -> bool:
        """
        验证插件配置。

        Returns:
            如果配置有效返回 True，否则返回 False。
        """
        return True

    def initialize(self) -> None:
        """初始化插件。插件加载时调用一次。"""
        pass

    def cleanup(self) -> None:
        """清理插件资源。插件卸载时调用。"""
        pass

    def get_info(self) -> PluginInfo:
        """获取插件信息作为 PluginInfo 对象。"""
        return PluginInfo(
            id=self.id,
            name=self.name,
            version=self.version,
            description=self.description,
            category=self.category,
            author=self.author,
            enabled=True,
            tags=self.tags,
            capabilities=self.capabilities,
            target_keywords=self.target_keywords
        )