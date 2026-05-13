"""
HTML渲染器工具函数测试
"""

import pytest

from ..renderer.html_renderer import (
    get_severity_color, truncate_text, calc_width,
    calc_pie_conic, calc_line_height
)


class TestGetSeverityColor:
    """验证严重程度到Bootstrap颜色的映射"""

    def test_info(self):
        assert get_severity_color('info') == 'secondary'

    def test_warning(self):
        assert get_severity_color('warning') == 'warning'

    def test_error(self):
        assert get_severity_color('error') == 'danger'

    def test_success(self):
        assert get_severity_color('success') == 'success'

    def test_unknown_returns_secondary(self):
        assert get_severity_color('unknown') == 'secondary'

    def test_empty_returns_secondary(self):
        assert get_severity_color('') == 'secondary'


class TestTruncateText:
    """验证文本截断逻辑"""

    def test_short_text_not_truncated(self):
        assert truncate_text("hello", 50) == "hello"

    def test_exact_length_not_truncated(self):
        text = "x" * 50
        assert truncate_text(text, 50) == text

    def test_long_text_truncated(self):
        text = "x" * 60
        result = truncate_text(text, 50)
        assert result == "x" * 50 + "..."
        assert len(result) == 53

    def test_empty_text(self):
        assert truncate_text("") == ""

    def test_none_text(self):
        assert truncate_text(None) == ''


class TestCalcWidth:
    """验证柱状图宽度百分比计算"""

    def test_normal_calculation(self):
        values = [10, 20, 30]
        assert calc_width(values, 2) == 100.0

    def test_first_bar(self):
        values = [5, 10]
        assert calc_width(values, 0) == 50.0

    def test_empty_list(self):
        assert calc_width([], 0) == 0

    def test_index_out_of_range(self):
        assert calc_width([10], 5) == 0

    def test_zero_max(self):
        assert calc_width([0, 0], 0) == 0


class TestCalcPieConic:
    """验证饼图 conic-gradient CSS 计算"""

    def test_empty_values(self):
        result = calc_pie_conic([])
        assert 'conic-gradient' in result
        assert '#dee2e6' in result

    def test_all_zeros(self):
        result = calc_pie_conic([0, 0])
        assert '#dee2e6' in result

    def test_normal_values(self):
        result = calc_pie_conic([50, 50])
        assert 'conic-gradient' in result
        assert '#0d6efd' in result
        assert '#198754' in result

    def test_single_value(self):
        result = calc_pie_conic([100])
        assert 'conic-gradient' in result
        assert '360' in result


class TestCalcLineHeight:
    """验证折线图柱高度计算"""

    def test_normal_calculation(self):
        values = [10, 20, 30]
        assert calc_line_height(values, 2, max_height=120) == 120

    def test_proportional(self):
        values = [10, 20]
        assert calc_line_height(values, 0, max_height=100) == 50

    def test_empty_values(self):
        assert calc_line_height([], 0) == 0

    def test_index_out_of_range(self):
        assert calc_line_height([10], 5) == 0

    def test_zero_max(self):
        assert calc_line_height([0, 0], 0) == 0
