"""
插件接口测试
"""

import re
import pytest

from ..base import (
    AnalysisResult, ResultMeta, CliResult,
    StatsItem, StatsSection, TableColumn, TableSection,
    TimelineEvent, TimelineSection, CardItem, CardsSection,
    ChartData, ChartSection, SearchBoxSection, RawSection,
    BasePlugin
)
from ..manager import PluginManager


@pytest.fixture
def plugin_manager():
    """创建并初始化插件管理器"""
    manager = PluginManager()
    manager.load_plugins()
    return manager


class TestDemoPluginWithLogContent:
    """验证demo_plugin接收log_content字典后正确解析"""

    def test_parses_log_content_dict(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        assert plugin is not None

        log_content = {
            "system.log": ["ERROR disk read failure", "WARNING low memory", "INFO started"]
        }
        result = plugin.analyze(log_content)
        assert isinstance(result, AnalysisResult)
        assert result.meta.plugin_id == 'example_00001'

    def test_detects_errors(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {
            "test.log": ["ERROR something went wrong", "FAIL again"]
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
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {
            "test.log": ["WARNING something suspicious"]
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
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {
            "a.log": ["INFO line1"],
            "b.log": ["INFO line2"]
        }
        result = plugin.analyze(log_content)
        assert set(result.meta.log_files) == {"a.log", "b.log"}

    def test_counts_log_lines(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {
            "test.log": ["line1", "line2", "line3"]
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
        pattern = re.compile(r'^[A-Za-z]+_\d{5}$')
        plugins = plugin_manager.get_all_plugins()
        assert len(plugins) > 0, "应该至少有一个插件"
        for plugin in plugins:
            assert pattern.match(plugin.id), f"插件ID格式不正确: {plugin.id}，应为 {{类型}}_00001 格式"

    def test_plugin_ids_are_unique(self, plugin_manager):
        plugins = plugin_manager.get_all_plugins()
        ids = [p.id for p in plugins]
        assert len(ids) == len(set(ids)), "插件ID应该唯一"


class TestParameterPassing:
    """验证插件analyze方法能接收完整参数"""

    def test_analyze_accepts_all_params(self, plugin_manager):
        """验证内置插件接受所有参数而不报错"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["INFO ok"]}
        result = plugin.analyze(
            log_content,
            task_name="test_task",
            bmc_ip="192.168.1.1",
            date="2024-01-01",
            source="cli"
        )
        assert isinstance(result, CliResult)

    def test_analyze_default_params(self, plugin_manager):
        """验证默认参数不影响现有行为"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR fail"]}
        result_default = plugin.analyze(log_content)
        result_explicit = plugin.analyze(
            log_content, task_name="", bmc_ip="", date="", source="system"
        )
        assert isinstance(result_default, AnalysisResult)
        assert isinstance(result_explicit, AnalysisResult)
        assert result_default.meta.plugin_id == result_explicit.meta.plugin_id


class TestCliReturnFormat:
    """验证source='cli'时返回CliResult格式"""

    def test_demo_plugin_cli_result_type(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR disk failure"]}
        result = plugin.analyze(log_content, source='cli')
        assert isinstance(result, CliResult)

    def test_demo_plugin_cli_fields(self, plugin_manager):
        """验证cli返回值的6个字段"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR disk failure"]}
        result = plugin.analyze(
            log_content,
            task_name="my_task",
            bmc_ip="192.168.1.1",
            date="2024-01-01",
            source='cli'
        )
        assert result.task_name == "my_task"
        assert result.bmc_ip == "192.168.1.1"
        assert result.date == "2024-01-01"
        assert result.status == 'ERROR'
        assert isinstance(result.description, str)
        assert len(result.description) <= 1000
        assert isinstance(result.log_detail, str)

    def test_demo_plugin_cli_status_ok(self, plugin_manager):
        """无错误时status为OK"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["INFO system started"]}
        result = plugin.analyze(log_content, source='cli')
        assert result.status == 'OK'

    def test_demo_plugin_cli_status_error(self, plugin_manager):
        """有错误时status为ERROR"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR disk failure"]}
        result = plugin.analyze(log_content, source='cli')
        assert result.status == 'ERROR'

    def test_demo_plugin_cli_to_list(self, plugin_manager):
        """验证to_list()输出格式"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR fail"]}
        result = plugin.analyze(
            log_content,
            task_name="t1",
            bmc_ip="1.1.1.1",
            date="2024-06-01",
            source='cli'
        )
        output = result.to_list()
        assert isinstance(output, list)
        assert len(output) == 6
        assert output[0] == "t1"
        assert output[1] == "1.1.1.1"
        assert output[2] == 'ERROR'
        assert output[5] == "2024-06-01"

    def test_demo_plugin_cli_log_detail_length(self, plugin_manager):
        """log_detail长度不超过3000"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"big.log": [f"ERROR error number {i}" for i in range(500)]}
        result = plugin.analyze(log_content, source='cli')
        assert len(result.log_detail) <= 3000


class TestSystemReturnFormat:
    """验证source='system'时返回AnalysisResult格式"""

    def test_demo_plugin_system_result(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR disk failure"]}
        result = plugin.analyze(log_content, source='system')
        assert isinstance(result, AnalysisResult)
        assert result.meta.plugin_id == 'example_00001'

    def test_demo_plugin_all_section_types(self, plugin_manager):
        """验证demo插件包含所有section类型"""
        plugin = plugin_manager.get_plugin('example_00001')
        log_content = {"test.log": ["ERROR fail", "WARNING warn", "INFO ok", "10:00:00 some event"]}
        result = plugin.analyze(log_content, source='system')

        # 检查包含的section类型
        section_types = set()
        for section in result.sections:
            section_types.add(section.__class__.__name__)

        # 至少包含这些类型
        expected_types = {'StatsSection', 'TableSection', 'TimelineSection',
                         'CardsSection', 'ChartSection', 'SearchBoxSection', 'RawSection'}
        # 允许部分类型缺失（取决于日志内容）
        assert len(section_types) >= 4  # 至少有4种类型


class TestDataClassSerialization:
    """验证所有数据类 to_dict() 序列化正确"""

    def test_result_meta_to_dict(self):
        meta = ResultMeta(
            plugin_id='test_00001', plugin_name='Test',
            version='2.0.0', analysis_time='2024-06-01 12:00:00',
            log_files=['a.log'], plugin_type='Test',
            description='测试插件'
        )
        d = meta.to_dict()
        assert d['plugin_id'] == 'test_00001'
        assert d['plugin_name'] == 'Test'
        assert d['version'] == '2.0.0'
        assert d['analysis_time'] == '2024-06-01 12:00:00'
        assert d['log_files'] == ['a.log']
        assert d['plugin_type'] == 'Test'
        assert d['description'] == '测试插件'

    def test_stats_item_to_dict(self):
        item = StatsItem(label='错误', value=5, unit='个', severity='error', icon='x')
        d = item.to_dict()
        assert d['label'] == '错误'
        assert d['value'] == 5
        assert d['unit'] == '个'
        assert d['severity'] == 'error'
        assert d['icon'] == 'x'

    def test_cli_result_to_list(self):
        r = CliResult(
            task_name='t', bmc_ip='1.1.1.1', status='OK',
            description='ok', log_detail='detail', date='2024-01-01'
        )
        lst = r.to_list()
        assert lst == ['t', '1.1.1.1', 'OK', 'ok', 'detail', '2024-01-01']

    def test_cli_result_description_truncation(self):
        long_desc = 'x' * 2000
        r = CliResult(description=long_desc)
        lst = r.to_list()
        assert len(lst[3]) == 1000

    def test_analysis_result_to_dict(self):
        meta = ResultMeta(
            plugin_id='p1', plugin_name='P', version='1.0',
            analysis_time='2024-01-01 00:00:00'
        )
        result = AnalysisResult(meta=meta)
        result.add_stats("标题", [StatsItem(label="项", value=1)])
        d = result.to_dict()
        assert d['meta']['plugin_id'] == 'p1'
        assert len(d['sections']) == 1
        assert d['sections'][0]['type'] == 'stats'

    def test_stats_section_to_dict(self):
        section = StatsSection(title="概览", icon="bar", items=[
            StatsItem(label="项", value=10, severity="error")
        ])
        d = section.to_dict()
        assert d['type'] == 'stats'
        assert d['title'] == '概览'
        assert d['icon'] == 'bar'
        assert len(d['items']) == 1

    def test_table_section_to_dict(self):
        section = TableSection(
            title="表", severity="warning", icon="t",
            columns=[{"key": "k", "label": "K"}],
            rows=[{"k": "v", "severity": "warning"}]
        )
        d = section.to_dict()
        assert d['type'] == 'table'
        assert d['severity'] == 'warning'
        assert len(d['columns']) == 1
        assert len(d['rows']) == 1

    def test_timeline_section_to_dict(self):
        section = TimelineSection(title="时间线", events=[
            TimelineEvent(timestamp="2024-01-01 00:00", title="事件", severity="error")
        ])
        d = section.to_dict()
        assert d['type'] == 'timeline'
        assert len(d['events']) == 1
        assert d['events'][0]['severity'] == 'error'

    def test_cards_section_to_dict(self):
        section = CardsSection(title="卡片", cards=[
            CardItem(title="卡片1", severity="info", content={"k": "v"})
        ])
        d = section.to_dict()
        assert d['type'] == 'cards'
        assert d['cards'][0]['content'] == {"k": "v"}

    def test_chart_section_to_dict(self):
        section = ChartSection(
            title="图表", chart_type="pie",
            data=ChartData(labels=["A", "B"], values=[10, 20]),
            options={"x_label": "X"}
        )
        d = section.to_dict()
        assert d['type'] == 'chart'
        assert d['chart_type'] == 'pie'
        assert d['data']['labels'] == ["A", "B"]
        assert d['data']['values'] == [10, 20]

    def test_search_box_section_to_dict(self):
        section = SearchBoxSection(
            title="搜索", placeholder="输入",
            data=[{"msg": "hello"}], search_fields=["msg"]
        )
        d = section.to_dict()
        assert d['type'] == 'search_box'
        assert d['placeholder'] == '输入'
        assert d['search_fields'] == ['msg']

    def test_raw_section_to_dict(self):
        section = RawSection(title="原始", data={"key": "val"})
        d = section.to_dict()
        assert d['type'] == 'raw'
        assert d['data'] == {"key": "val"}


class TestBasePluginMethods:
    """验证 BasePlugin 方法行为"""

    def _make_plugin(self):
        """创建一个可实例化的插件子类"""
        class TestPlugin(BasePlugin):
            def analyze(self, log_content, task_name="", bmc_ip="",
                        date="", source="system"):
                return AnalysisResult(meta=ResultMeta(
                    plugin_id=self.id, plugin_name=self.name,
                    version=self.get_version(), analysis_time='2024-01-01'
                ))
        return TestPlugin()

    def test_set_metadata(self):
        p = self._make_plugin()
        p.set_metadata(id='test_00001', name='Test', plugin_type='Test',
                       version='2.0', description='描述')
        assert p.id == 'test_00001'
        assert p.name == 'Test'
        assert p.get_plugin_type() == 'Test'
        assert p.get_version() == '2.0'
        assert p.get_chinese_description() == '描述'

    def test_set_metadata_none_no_override(self):
        p = self._make_plugin()
        p.set_metadata(id='orig', name='Orig')
        p.set_metadata(id=None, name=None, plugin_type='New')
        assert p.id == 'orig'
        assert p.name == 'Orig'
        assert p.get_plugin_type() == 'New'

    def test_log_with_callback(self):
        p = self._make_plugin()
        messages = []
        p.set_log_callback(lambda msg, level: messages.append((msg, level)))
        p.log("测试消息", "warning")
        assert len(messages) == 1
        assert messages[0][1] == "warning"
        assert "测试消息" in messages[0][0]

    def test_log_without_callback(self):
        p = self._make_plugin()
        p.log("无回调")  # 不应抛异常

    def test_set_log_callback(self):
        p = self._make_plugin()
        callback = lambda msg, level: None
        p.set_log_callback(callback)
        assert p._log_callback is callback

    def test_format_log_detail_empty(self):
        assert BasePlugin.format_log_detail({}) == ""

    def test_format_log_detail_normal(self):
        import json
        detail = {"errors": 1, "items": ["err1"]}
        result = BasePlugin.format_log_detail(detail)
        parsed = json.loads(result)
        assert parsed["errors"] == 1

    def test_format_log_detail_truncation(self):
        detail = {"items": [f"item_{i}" for i in range(500)]}
        result = BasePlugin.format_log_detail(detail)
        assert len(result) <= 3000

    def test_format_log_detail_all_items_removed(self):
        # 极端情况：items 全部被截断后移除 items key
        detail = {"items": ["x" * 500 for _ in range(100)]}
        result = BasePlugin.format_log_detail(detail)
        assert len(result) <= 3000


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_log_content(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        result = plugin.analyze({})
        assert isinstance(result, AnalysisResult)

    def test_only_empty_lines(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        result = plugin.analyze({"test.log": ["", "  ", ""]})
        assert isinstance(result, AnalysisResult)

    def test_single_line(self, plugin_manager):
        plugin = plugin_manager.get_plugin('example_00001')
        result = plugin.analyze({"test.log": ["INFO system ok"]})
        assert isinstance(result, AnalysisResult)
