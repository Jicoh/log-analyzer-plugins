"""
日志统计插件。

展示 stats 和 chart 类型的返回值。
"""

import os
import re
from collections import Counter
from datetime import datetime

from plugins.base import (
    BasePlugin, AnalysisResult, ResultMeta, StatsItem, ChartData
)


class LogStatisticsPlugin(BasePlugin):
    """日志统计插件。"""

    def analyze(self, log_file: str) -> AnalysisResult:
        """分析日志统计信息。"""
        self.log("开始统计分析...")

        # 读取日志
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        self.log(f"读取到 {len(lines)} 行日志")

        # 统计日志级别分布
        level_counter = Counter()
        for line in lines:
            line_upper = line.upper()
            for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                if level in line_upper:
                    level_counter[level] += 1
                    break

        # 统计时间分布
        hour_counter = Counter()
        for line in lines:
            match = re.search(r'(\d{2}):\d{2}:\d{2}', line)
            if match:
                hour = match.group(1)
                hour_counter[f"{hour}:00"] += 1

        self.log("统计完成")

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
        file_size = os.path.getsize(log_file)
        result.add_stats("文件信息", [
            StatsItem(label="总行数", value=len(lines), unit="行", severity="info", icon="file-text"),
            StatsItem(label="文件大小", value=f"{file_size/1024:.1f}", unit="KB", severity="info", icon="hard-drive")
        ])

        # 添加日志级别分布图表
        if level_counter:
            result.add_chart("日志级别分布", chart_type="bar",
                data=ChartData(
                    labels=list(level_counter.keys()),
                    values=list(level_counter.values())
                ),
                options={"x_label": "级别", "y_label": "数量"}
            )

        # 添加时间分布图表
        if hour_counter:
            sorted_hours = sorted(hour_counter.items())[:12]
            result.add_chart("时间分布", chart_type="line",
                data=ChartData(
                    labels=[h[0] for h in sorted_hours],
                    values=[h[1] for h in sorted_hours]
                ),
                options={"x_label": "时间", "y_label": "日志数"},
                icon="clock"
            )

        return result


# 导出插件类
plugin_class = LogStatisticsPlugin