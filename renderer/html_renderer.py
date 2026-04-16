"""
插件分析结果HTML渲染器。

将JSON格式的插件分析结果转换为独立的静态HTML文件，按插件分类展示。
"""

import os
import json
from jinja2 import Template
from plugins.base import count_severity

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'template.html')
BATCH_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'batch_template.html')


def get_severity_color(severity: str) -> str:
    """获取严重程度对应的Bootstrap颜色。"""
    colors = {
        'info': 'secondary',
        'warning': 'warning',
        'error': 'danger',
        'success': 'success'
    }
    return colors.get(severity, 'secondary')


def get_chart_color(index: int) -> str:
    """获取图表颜色。"""
    colors = ['primary', 'success', 'warning', 'danger', 'info', 'secondary']
    return colors[index % len(colors)]


def get_chart_hex_color(index: int) -> str:
    """获取图表颜色的十六进制值。"""
    colors = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6c757d']
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


def calc_pie_conic(values: list) -> str:
    """计算饼图的 conic-gradient CSS 值。"""
    if not values:
        return 'conic-gradient(#dee2e6 0deg, #dee2e6 360deg)'
    colors = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#0dcaf0', '#6c757d']
    total = sum(values)
    if total == 0:
        return 'conic-gradient(#dee2e6 0deg, #dee2e6 360deg)'

    segments = []
    current_angle = 0
    for i, val in enumerate(values):
        angle = (val / total) * 360
        color = colors[i % len(colors)]
        segments.append(f'{color} {current_angle}deg {current_angle + angle}deg')
        current_angle += angle
    return f'conic-gradient({", ".join(segments)})'


def calc_line_height(values: list, index: int, max_height: int = 120) -> int:
    """计算折线图柱高度（像素），放大到指定最大高度。"""
    if not values or index >= len(values):
        return 0
    max_val = max(values) if values else 1
    return int((values[index] / max_val) * max_height) if max_val > 0 else 0


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
            get_chart_hex_color=get_chart_hex_color,
            calc_width=calc_width,
            truncate_text=truncate_text,
            calc_pie_conic=calc_pie_conic,
            calc_line_height=calc_line_height
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


def render_batch_html(summary_path: str) -> str:
    """
    读取批量汇总JSON文件并生成汇总HTML。

    Args:
        summary_path: batch_summary.json 文件路径

    Returns:
        生成的batch_summary.html文件路径
    """
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_data = json.load(f)

    # 加载批量模板
    with open(BATCH_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = Template(f.read())

    # 提取文件列表信息
    files_info = []
    for filename, file_data in summary_data.get('files', {}).items():
        # 计算错误和警告数
        total_errors = 0
        total_warnings = 0
        plugin_count = 0

        plugin_result = file_data.get('plugin_result', {})
        for plugin_id, plugin_data in plugin_result.items():
            if isinstance(plugin_data, dict):
                plugin_count += 1
                sections = plugin_data.get('sections', [])
                counts = count_severity(sections)
                total_errors += counts['errors']
                total_warnings += counts['warnings']

        files_info.append({
            'filename': filename,
            'output_dir': file_data.get('output_dir', ''),
            'html_path': file_data.get('html_path', ''),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'plugin_count': plugin_count,
            'has_ai': file_data.get('ai_result') is not None
        })

    # 构建模板数据
    template_data = {
        'batch_time': summary_data.get('batch_time', ''),
        'folder_name': summary_data.get('folder_name', ''),
        'total_files': summary_data.get('total_files', 0),
        'files': files_info
    }

    html_content = template.render(**template_data)

    output_dir = os.path.dirname(summary_path)
    output_path = os.path.join(output_dir, 'batch_summary.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path