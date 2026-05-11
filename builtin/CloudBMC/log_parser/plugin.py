"""
日志解析插件。

展示 stats 和 table 类型的返回值。
"""

from datetime import datetime
from typing import Dict, List, Union

from plugins.base import (
    BasePlugin, AnalysisResult, ResultMeta, StatsItem, CliResult
)


class LogParserPlugin(BasePlugin):
    """日志解析插件。"""

    def analyze(self, log_content: Dict[str, List[str]],
                task_name: str = "", bmc_ip: str = "", date: str = "",
                source: str = "system") -> Union[AnalysisResult, CliResult]:
        """分析日志内容。"""
        self.log("开始解析日志...")

        # 从log_content字典中提取所有行
        all_lines = []
        for log_name, lines in log_content.items():
            all_lines.extend(lines)

        self.log(f"读取到 {len(all_lines)} 行日志")

        # 统计错误和警告
        errors = []
        warnings = []

        for i, line in enumerate(all_lines, 1):
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
            log_files=list(log_content.keys()),
            plugin_type=self.get_plugin_type(),
            description=self.get_chinese_description()
        )

        result = AnalysisResult(meta=meta)

        # 添加统计概览
        result.add_stats("分析概览", [
            StatsItem(label="总行数", value=len(all_lines), unit="行", severity="info", icon="file-text"),
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

        # 同时构建cli格式返回值
        cli_result = CliResult(
            task_name=task_name,
            bmc_ip=bmc_ip,
            status='ERROR' if errors else 'OK',
            description=self._build_cli_description(errors, warnings),
            log_detail=self._build_cli_log_detail(errors, warnings),
            date=date
        )

        if source == 'cli':
            return cli_result
        return result

    def _build_cli_description(self, errors: list, warnings: list) -> str:
        """构建cli模式的描述信息"""
        parts = []
        if errors:
            parts.append(f"错误数: {len(errors)}")
        if warnings:
            parts.append(f"警告数: {len(warnings)}")
        # 附加前几条错误消息
        for err in errors[:5]:
            msg = err.get('message', '')
            if msg:
                parts.append(msg[:100])
        return '; '.join(parts)[:1000]

    def _build_cli_log_detail(self, errors: list, warnings: list) -> str:
        """构建cli模式的日志详情"""
        detail = {}
        if errors or warnings:
            detail['errors'] = len(errors)
            detail['warnings'] = len(warnings)
            items = errors[:20] + warnings[:20]
            if items:
                detail['items'] = items
        return self.format_log_detail(detail)


# 导出插件类
plugin_class = LogParserPlugin
