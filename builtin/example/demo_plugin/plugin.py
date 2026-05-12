"""
示例插件 - 展示所有返回值类型。

本插件展示所有 7 种 section 类型：
- stats: 统计概览
- table: 数据表格
- timeline: 时间线
- cards: 卡片展示
- chart: 图表（bar/pie/line）
- search_box: 搜索框
- raw: 原始 JSON 数据
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Union

from plugins.base import (
    BasePlugin, AnalysisResult, ResultMeta, StatsItem,
    TimelineEvent, CardItem, ChartData, CliResult
)


class DemoPlugin(BasePlugin):
    """示例插件，展示所有返回值类型。"""

    def analyze(self, log_content: Dict[str, List[str]],
                task_name: str = "", bmc_ip: str = "", date: str = "",
                source: str = "system") -> Union[AnalysisResult, CliResult]:
        """分析日志内容，展示所有 section 类型。"""
        self.log("开始示例分析...")

        # 从 log_content 字典中提取所有行
        all_lines = []
        for log_name, lines in log_content.items():
            all_lines.extend(lines)

        self.log(f"读取到 {len(all_lines)} 行日志")

        # 解析日志内容
        errors, warnings, info_lines = self._parse_logs(all_lines)
        level_counter, hour_counter = self._count_levels_and_hours(all_lines)

        # 创建元数据
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

        # ========== 1. Stats 统计概览 ==========
        result.add_stats("统计概览", [
            StatsItem(label="总行数", value=len(all_lines), unit="行", severity="info", icon="file-text"),
            StatsItem(label="错误数", value=len(errors), unit="个", severity="error", icon="x-circle"),
            StatsItem(label="警告数", value=len(warnings), unit="个", severity="warning", icon="alert-triangle"),
            StatsItem(label="信息数", value=len(info_lines), unit="条", severity="info", icon="info"),
        ], icon="chart-bar")

        # ========== 2. Table 数据表格 ==========
        if errors:
            result.add_table("错误详情",
                columns=[
                    {"key": "line", "label": "行号", "type": "number", "width": "10%"},
                    {"key": "message", "label": "消息", "type": "text", "truncate": 80}
                ],
                rows=errors[:20],
                severity="error",
                icon="x-circle")

        # ========== 3. Timeline 时间线 ==========
        events = self._build_timeline(events=errors[:5] + warnings[:5])
        if events:
            result.add_timeline("事件时间线", events, icon="clock")

        # ========== 4. Cards 卡片展示 ==========
        cards = self._build_cards(errors, warnings, level_counter)
        result.add_cards("问题分类", cards, icon="layers")

        # ========== 5. Chart 图表 ==========
        if level_counter:
            result.add_chart("日志级别分布",
                chart_type="bar",
                data=ChartData(
                    labels=list(level_counter.keys()),
                    values=list(level_counter.values())
                ),
                options={"x_label": "级别", "y_label": "数量"},
                icon="chart-bar")

        if hour_counter:
            sorted_hours = sorted(hour_counter.items())[:12]
            result.add_chart("时间分布",
                chart_type="line",
                data=ChartData(
                    labels=[h[0] for h in sorted_hours],
                    values=[h[1] for h in sorted_hours]
                ),
                options={"x_label": "时间", "y_label": "日志数"},
                icon="clock")

        # ========== 6. SearchBox 搜索框 ==========
        search_data = self._build_search_data(errors + warnings + info_lines[:10])
        if search_data:
            result.add_search_box("日志搜索",
                data=search_data,
                search_fields=["line", "level", "message"],
                placeholder="输入关键字搜索日志...",
                icon="search")

        # ========== 7. Raw 原始数据 ==========
        result.add_raw("原始统计", data={
            "level_distribution": dict(level_counter),
            "hour_distribution": dict(hour_counter),
            "file_count": len(log_content.keys())
        })

        self.log("分析完成")

        # 构建 cli 格式返回值
        cli_result = CliResult(
            task_name=task_name,
            bmc_ip=bmc_ip,
            status='ERROR' if errors else 'OK',
            description=self._build_cli_description(errors, warnings, len(all_lines)),
            log_detail=self._build_cli_log_detail(errors, warnings),
            date=date
        )

        if source == 'cli':
            return cli_result
        return result

    def _parse_logs(self, lines: List[str]) -> tuple:
        """解析日志，分类错误、警告和信息。"""
        errors = []
        warnings = []
        info_lines = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            if 'error' in line.lower() or 'fail' in line.lower():
                errors.append({'line': i, 'message': line[:100], 'severity': 'error'})
            elif 'warn' in line.lower():
                warnings.append({'line': i, 'message': line[:100], 'severity': 'warning'})
            elif 'info' in line.lower():
                info_lines.append({'line': i, 'message': line[:100], 'severity': 'info'})

        return errors, warnings, info_lines

    def _count_levels_and_hours(self, lines: List[str]) -> tuple:
        """统计日志级别和时间分布。"""
        level_counter = Counter()
        hour_counter = Counter()

        for line in lines:
            # 统计级别
            line_upper = line.upper()
            for level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
                if level in line_upper:
                    level_counter[level] += 1
                    break

            # 统计时间
            match = re.search(r'(\d{2}):\d{2}:\d{2}', line)
            if match:
                hour = match.group(1)
                hour_counter[f"{hour}:00"] += 1

        return level_counter, hour_counter

    def _build_timeline(self, events: List[Dict]) -> List[TimelineEvent]:
        """构建时间线事件。"""
        timeline_events = []
        now = datetime.now().strftime('%Y-%m-%d')

        for i, event in enumerate(events[:10]):
            severity = event.get('severity', 'info')
            timeline_events.append(TimelineEvent(
                timestamp=f"{now} {10 + i}:00:00",
                title=event.get('message', '')[:50],
                description=event.get('message', ''),
                severity=severity,
                icon="x-circle" if severity == 'error' else "alert-triangle" if severity == 'warning' else "info",
                detail=f"行号: {event.get('line', 'N/A')}"
            ))

        return timeline_events

    def _build_cards(self, errors: List, warnings: List, level_counter: Counter) -> List[CardItem]:
        """构建问题分类卡片。"""
        cards = []

        if errors:
            cards.append(CardItem(
                title="错误问题",
                severity="error",
                icon="x-circle",
                content={
                    "summary": f"发现 {len(errors)} 个错误",
                    "description": "需要关注的错误日志",
                    "metrics": {"错误数": len(errors)}
                }
            ))

        if warnings:
            cards.append(CardItem(
                title="警告问题",
                severity="warning",
                icon="alert-triangle",
                content={
                    "summary": f"发现 {len(warnings)} 个警告",
                    "description": "需要关注的警告日志",
                    "metrics": {"警告数": len(warnings)}
                }
            ))

        cards.append(CardItem(
            title="日志概览",
            severity="success" if not errors else "warning",
            icon="chart-bar",
            content={
                "summary": "日志分析完成",
                "description": "所有日志已解析",
                "metrics": dict(level_counter)
            }
        ))

        return cards

    def _build_search_data(self, items: List[Dict]) -> List[Dict]:
        """构建搜索数据。"""
        search_data = []
        for item in items:
            search_data.append({
                "line": item.get('line', ''),
                "level": item.get('severity', 'info').upper(),
                "message": item.get('message', '')[:50]
            })
        return search_data

    def _build_cli_description(self, errors: List, warnings: List, total_lines: int) -> str:
        """构建 cli 模式的描述信息。"""
        parts = [f"总行数: {total_lines}"]
        if errors:
            parts.append(f"错误数: {len(errors)}")
        if warnings:
            parts.append(f"警告数: {len(warnings)}")
        for err in errors[:3]:
            parts.append(err.get('message', '')[:50])
        return '; '.join(parts)[:1000]

    def _build_cli_log_detail(self, errors: List, warnings: List) -> str:
        """构建 cli 模式的日志详情。"""
        detail = {
            'errors': len(errors),
            'warnings': len(warnings),
            'items': (errors + warnings)[:20]
        }
        return self.format_log_detail(detail)


# 导出插件类
plugin_class = DemoPlugin
