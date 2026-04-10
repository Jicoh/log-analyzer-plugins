"""
Plugin system for AI Log Analyzer.
"""

from plugins.base import (
    BasePlugin, Severity, AnalysisResult, ResultMeta,
    StatsItem, StatsSection, TableSection, TableColumn, TimelineEvent, TimelineSection,
    CardItem, CardsSection, ChartData, ChartSection, SearchBoxSection, RawSection,
    SectionType
)
from plugins.manager import PluginManager, get_plugin_manager

__all__ = [
    'BasePlugin',
    'Severity',
    'AnalysisResult',
    'ResultMeta',
    'StatsItem',
    'StatsSection',
    'TableSection',
    'TableColumn',
    'TimelineEvent',
    'TimelineSection',
    'CardItem',
    'CardsSection',
    'ChartData',
    'ChartSection',
    'SearchBoxSection',
    'RawSection',
    'SectionType',
    'PluginManager',
    'get_plugin_manager',
]