"""
插件分析结果HTML渲染器。

将JSON格式的插件分析结果转换为独立的静态HTML文件，按插件分类展示。
"""

import os
import json
from jinja2 import Template

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'template.html')


def get_severity_color(severity: str) -> str:
    """获取严重程度对应的Bootstrap颜色。"""
    colors = {
        'info': 'secondary',
        'warning': 'warning',
        'error': 'danger',
        'critical': 'danger',
        'success': 'success'
    }
    return colors.get(severity, 'secondary')


def get_chart_color(index: int) -> str:
    """获取图表颜色。"""
    colors = ['primary', 'success', 'warning', 'danger', 'info', 'secondary']
    return colors[index % len(colors)]


def calc_width(values: list, index: int) -> float:
    """计算柱状图宽度百分比。"""
    if not values or index >= len(values):
        return 0
    max_val = max(values) if values else 1
    return (values[index] / max_val * 100) if max_val > 0 else 0


def truncate_text(text: str, max_len: int = 50) -> str:
    """截断文本。"""
    if not text:
        return ''
    return text[:max_len] + '...' if len(text) > max_len else text


def render_html(json_path: str) -> str:
    """
    读取JSON文件并生成HTML文件到同目录。

    Args:
        json_path: JSON文件路径

    Returns:
        生成的HTML文件路径
    """
    renderer = HtmlRenderer()
    return renderer.render_to_file(json_path)


class HtmlRenderer:
    """插件分析结果HTML渲染器。"""

    def __init__(self):
        self.template = self._load_template()

    def _load_template(self) -> Template:
        """加载HTML模板。"""
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            return Template(f.read())

    def render(self, data: dict) -> str:
        """
        将JSON数据渲染为HTML字符串。

        Args:
            data: 插件分析结果数据（按插件ID为key的字典）

        Returns:
            HTML字符串
        """
        return self.template.render(
            result=data,
            get_severity_color=get_severity_color,
            get_chart_color=get_chart_color,
            calc_width=calc_width,
            truncate_text=truncate_text
        )

    def render_to_file(self, json_path: str) -> str:
        """
        读取JSON文件并生成HTML文件到同目录。

        Args:
            json_path: JSON文件路径

        Returns:
            生成的HTML文件路径
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        html_content = self.render(data)

        output_dir = os.path.dirname(json_path)
        output_path = os.path.join(output_dir, 'plugin_result.html')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path