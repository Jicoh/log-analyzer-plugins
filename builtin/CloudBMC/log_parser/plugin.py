"""
日志解析插件。

展示 stats 和 table 类型的返回值。
"""

import os
from datetime import datetime

from plugins.base import (
    BasePlugin, AnalysisResult, ResultMeta, StatsItem
)


class LogParserPlugin(BasePlugin):
    """日志解析插件。"""

    def analyze(self, log_file: str) -> AnalysisResult:
        """分析日志文件。"""
        self.log("开始解析日志文件...")

        # 读取日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        self.log(f"读取到 {len(lines)} 行日志")

        # 统计错误和警告
        errors = []
        warnings = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if 'error' in line.lower() or 'fail' in line.lower():
                errors.append({
                    'line': i,
                    'message': line[:100],
                    'severity': 'error'
                })
            elif 'warn' in line.lower():
                warnings.append({
                    'line': i,
                    'message': line[:100],
                    'severity': 'warning'
                })

        self.log(f"发现 {len(errors)} 个错误, {len(warnings)} 个警告")

        # 创建结果
        meta = ResultMeta(
            plugin_id=self.id,
            plugin_name=self.name,
            version=self.get_version(),
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            log_file=os.path.basename(log_file),
            plugin_type=self.get_plugin_type()
        )

        result = AnalysisResult(meta=meta)

        # 添加统计概览
        result.add_stats("分析概览", [
            StatsItem(label="总行数", value=len(lines), unit="行", severity="info", icon="file-text"),
            StatsItem(label="错误数", value=len(errors), unit="个", severity="error", icon="x-circle"),
            StatsItem(label="警告数", value=len(warnings), unit="个", severity="warning", icon="alert-triangle")
        ])

        # 添加错误表格
        if errors:
            result.add_table("错误详情",
                columns=[
                    {"key": "line", "label": "行号", "type": "number"},
                    {"key": "message", "label": "消息", "type": "text"}
                ],
                rows=errors[:50],
                severity="error",
                icon="x-circle"
            )

        # 添加警告表格
        if warnings:
            result.add_table("警告详情",
                columns=[
                    {"key": "line", "label": "行号", "type": "number"},
                    {"key": "message", "label": "消息", "type": "text"}
                ],
                rows=warnings[:50],
                severity="warning",
                icon="alert-triangle"
            )

        self.log("分析完成")
        return result


# 导出插件类
plugin_class = LogParserPlugin