"""
日志统计插件。

展示 stats 和 chart 类型的返回值。
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Union

from plugins.base import (
    BasePlugin, AnalysisResult, ResultMeta, StatsItem, ChartData, CliResult
)


class LogStatisticsPlugin(BasePlugin):
    """日志统计插件。"""

    def analyze(self, log_content: Dict[str, List[str]],
                task_name: str = "", bmc_ip: str = "", date: str = "",
                source: str = "system") -> Union[AnalysisResult, CliResult]:
        """分析日志统计信息。"""
        self.log("开始统计分析...")

        # 从log_content字典中提取所有行
        all_lines = []
        total_size = 0
        for log_name, lines in log_content.items():
            all_lines.extend(lines)
            total_size += sum(len(line.encode('utf-8')) for line in lines)

        self.log(f"读取到 {len(all_lines)} 行日志")

        # 统计日志级别分布
        level_counter = Counter()
        for line in all_lines:
            line_upper = line.upper()
            for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                if level in line_upper:
                    level_counter[level] += 1
                    break

        # 统计时间分布
        hour_counter = Counter()
        for line in all_lines:
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
            log_files=list(log_content.keys()),
            plugin_type=self.get_plugin_type(),
            description=self.get_chinese_description()
        )

        result = AnalysisResult(meta=meta)

        # 添加统计概览
        result.add_stats("文件信息", [
            StatsItem(label="总行数", value=len(all_lines), unit="行", severity="info", icon="file-text"),
            StatsItem(label="文件大小", value=f"{total_size/1024:.1f}", unit="KB", severity="info", icon="hard-drive")
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

        # 同时构建cli格式返回值
        error_count = level_counter.get('ERROR', 0)
        cli_result = CliResult(
            task_name=task_name,
            bmc_ip=bmc_ip,
            status='ERROR' if error_count > 0 else 'OK',
            description=self._build_cli_description(level_counter, len(all_lines), total_size),
            log_detail=self._build_cli_log_detail(level_counter),
            date=date
        )

        if source == 'cli':
            return cli_result
        return result

    def _build_cli_description(self, level_counter: Counter, total_lines: int, total_size: int) -> str:
        """构建cli模式的描述信息"""
        parts = [f"总行数: {total_lines}", f"文件大小: {total_size/1024:.1f}KB"]
        for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if level in level_counter:
                parts.append(f"{level}: {level_counter[level]}")
        return '; '.join(parts)[:1000]

    def _build_cli_log_detail(self, level_counter: Counter) -> str:
        """构建cli模式的日志详情"""
        return self.format_log_detail(dict(level_counter))


# 导出插件类
plugin_class = LogStatisticsPlugin
