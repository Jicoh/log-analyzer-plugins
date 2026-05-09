"""
插件接口测试
"""

import re
import pytest

from plugins.manager import PluginManager
from plugins.base import AnalysisResult, ResultMeta


@pytest.fixture
def plugin_manager():
    """创建并初始化插件管理器"""
    manager = PluginManager()
    manager.load_plugins()
    return manager


class TestLogParserWithLogContent:
    """验证log_parser接收log_content字典后正确解析"""

    def test_parses_log_content_dict(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00001')
        assert plugin is not None

        log_content = {
            "system.log": "ERROR disk read failure\nWARNING low memory\nINFO started"
        }
        result = plugin.analyze(log_content)
        assert isinstance(result, AnalysisResult)
        assert result.meta.plugin_id == 'CloudBMC_00001'

    def test_detects_errors(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00001')
        log_content = {
            "test.log": "ERROR something went wrong\nFAIL again"
        }
        result = plugin.analyze(log_content)
        # 检查sections中有error相关的统计
        found_error_stat = False
        for section in result.sections:
            if hasattr(section, 'items'):
                for item in section.items:
                    if item.severity == 'error' and item.value > 0:
                        found_error_stat = True
        assert found_error_stat

    def test_detects_warnings(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00001')
        log_content = {
            "test.log": "WARNING something suspicious"
        }
        result = plugin.analyze(log_content)
        found_warning_stat = False
        for section in result.sections:
            if hasattr(section, 'items'):
                for item in section.items:
                    if item.severity == 'warning' and item.value > 0:
                        found_warning_stat = True
        assert found_warning_stat

    def test_log_files_in_meta(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00001')
        log_content = {
            "a.log": "INFO line1",
            "b.log": "INFO line2"
        }
        result = plugin.analyze(log_content)
        assert set(result.meta.log_files) == {"a.log", "b.log"}


class TestLogStatisticsWithLogContent:
    """验证log_statistics接收log_content字典后正确统计"""

    def test_parses_log_content_dict(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00002')
        assert plugin is not None

        log_content = {
            "system.log": "ERROR disk failure\nWARNING low memory\nINFO started"
        }
        result = plugin.analyze(log_content)
        assert isinstance(result, AnalysisResult)
        assert result.meta.plugin_id == 'CloudBMC_00002'

    def test_counts_log_lines(self, plugin_manager):
        plugin = plugin_manager.get_plugin('CloudBMC_00002')
        log_content = {
            "test.log": "line1\nline2\nline3"
        }
        result = plugin.analyze(log_content)
        # 检查总行数统计
        for section in result.sections:
            if hasattr(section, 'items'):
                for item in section.items:
                    if item.label == '总行数':
                        assert item.value == 3


class TestPluginIdFormat:
    """验证所有插件ID符合 {类型}_00001 格式"""

    def test_plugin_id_format(self, plugin_manager):
        import re
        pattern = re.compile(r'^(CloudBMC|iBMC|LxBMC)_\d{5}$')
        plugins = plugin_manager.get_all_plugins()
        assert len(plugins) > 0, "应该至少有一个插件"
        for plugin in plugins:
            assert pattern.match(plugin.id), f"插件ID格式不正确: {plugin.id}，应为 {{类型}}_00001 格式"

    def test_plugin_ids_are_unique(self, plugin_manager):
        plugins = plugin_manager.get_all_plugins()
        ids = [p.id for p in plugins]
        assert len(ids) == len(set(ids)), "插件ID应该唯一"
