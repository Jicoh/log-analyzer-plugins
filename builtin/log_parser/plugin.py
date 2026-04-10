"""
日志解析插件

内置插件，用于解析日志文件并提取错误、警告和统计数据。
"""

import re
import os
from datetime import datetime
from collections import Counter
from typing import Dict, Any, List

from plugins.base import BasePlugin, PluginCategory, AnalysisResult


class LogParserPlugin(BasePlugin):
    """BMC 日志解析插件。"""

    # 常见日志级别
    LOG_LEVELS = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL', 'FATAL']

    # 常见错误模式
    ERROR_PATTERNS = [
        r'error',
        r'fail',
        r'exception',
        r'critical',
        r'fatal',
        r'fault',
        r'abort',
        r'timeout',
        r'overflow',
        r'underflow',
        r'corrupt'
    ]

    # 常见警告模式
    WARNING_PATTERNS = [
        r'warn',
        r'warning',
        r'degrad',
        r'retry',
        r'unavailable',
        r'threshold',
        r'limit'
    ]

    @property
    def id(self) -> str:
        return "log_parser"

    @property
    def name(self) -> str:
        return "Log Parser"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Parse log files and extract errors, warnings, and statistics"

    @property
    def category(self) -> PluginCategory:
        return PluginCategory.PARSER

    @property
    def author(self) -> str:
        return "AI Log Analyzer Team"

    @property
    def tags(self) -> List[str]:
        return ["log", "parser", "error", "warning", "bmc"]

    @property
    def capabilities(self) -> List[str]:
        return ["error_detection", "warning_extraction", "log_parsing", "component_analysis"]

    @property
    def target_keywords(self) -> List[str]:
        return ["error", "warning", "fail", "crash", "exception", "memory", "leak",
                "critical", "fatal", "timeout", "bmc", "sel", "sensor"]

    def analyze(self, log_file: str) -> AnalysisResult:
        """
        分析日志文件。

        Args:
            log_file: 日志文件路径。

        Returns:
            包含分析结果的 AnalysisResult。
        """
        analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_filename = os.path.basename(log_file)

        # 读取并解析日志文件
        lines = self.read_log_file(log_file)
        parsed_lines = self.parse_lines(lines)

        # 提取错误和警告
        errors = self.extract_errors(parsed_lines)
        warnings = self.extract_warnings(parsed_lines)

        # 计算统计数据
        statistics = self.calculate_statistics(lines, parsed_lines, len(errors), len(warnings))

        return AnalysisResult(
            plugin_id=self.id,
            plugin_name=self.name,
            analysis_time=analysis_time,
            log_file=log_filename,
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            statistics=statistics
        )

    def read_log_file(self, log_file: str) -> List[str]:
        """读取日志文件内容。"""
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()

    def parse_lines(self, lines: List[str]) -> List[Dict[str, Any]]:
        """解析日志行。"""
        parsed = []
        for line_num, line in enumerate(lines, 1):
            parsed_line = self.parse_line(line.strip(), line_num)
            if parsed_line:
                parsed.append(parsed_line)
        return parsed

    def parse_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """解析单行日志。"""
        if not line:
            return None

        result = {
            'line_number': line_num,
            'raw': line,
            'timestamp': '',
            'level': '',
            'component': '',
            'message': ''
        }

        # 尝试提取时间戳
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{2}:\d{2}:\d{2})',
            r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\]'
        ]

        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                result['timestamp'] = match.group(1)
                break

        # 提取日志级别
        line_upper = line.upper()
        for level in self.LOG_LEVELS:
            if level in line_upper:
                result['level'] = level
                break

        # 提取组件名（方括号中的内容）
        component_match = re.search(r'\[([^\]]+)\]', line)
        if component_match:
            component = component_match.group(1)
            if component and not re.match(r'^\d{4}-\d{2}-\d{2}', component):
                result['component'] = component

        # 提取消息
        result['message'] = line

        return result

    def extract_errors(self, parsed_lines: List[Dict]) -> List[Dict]:
        """提取错误信息。"""
        errors = []
        error_pattern = re.compile('|'.join(self.ERROR_PATTERNS), re.IGNORECASE)

        for line_info in parsed_lines:
            if line_info['level'] in ['ERROR', 'CRITICAL', 'FATAL']:
                errors.append(self.format_issue(line_info))
            elif error_pattern.search(line_info['message']):
                # 避免重复
                if line_info['level'] not in ['WARN', 'WARNING']:
                    errors.append(self.format_issue(line_info))

        return errors

    def extract_warnings(self, parsed_lines: List[Dict]) -> List[Dict]:
        """提取警告信息。"""
        warnings = []
        warning_pattern = re.compile('|'.join(self.WARNING_PATTERNS), re.IGNORECASE)

        for line_info in parsed_lines:
            if line_info['level'] in ['WARN', 'WARNING']:
                warnings.append(self.format_issue(line_info))
            elif warning_pattern.search(line_info['message']):
                # 避免与错误重复
                if line_info['level'] not in ['ERROR', 'CRITICAL', 'FATAL']:
                    warnings.append(self.format_issue(line_info))

        return warnings

    def format_issue(self, line_info: Dict) -> Dict:
        """格式化问题信息。"""
        return {
            'timestamp': line_info['timestamp'],
            'level': line_info['level'] or 'UNKNOWN',
            'message': line_info['message'],
            'component': line_info['component'],
            'line_number': line_info['line_number']
        }

    def calculate_statistics(
        self,
        lines: List[str],
        parsed_lines: List[Dict],
        error_count: int,
        warning_count: int
    ) -> Dict[str, Any]:
        """计算统计数据。"""
        total_lines = len(lines)
        level_counter = Counter()
        component_counter = Counter()

        for line_info in parsed_lines:
            if line_info['level']:
                level_counter[line_info['level']] += 1
            if line_info['component']:
                component_counter[line_info['component']] += 1

        return {
            'total_lines': total_lines,
            'error_rate': round(error_count / total_lines, 6) if total_lines > 0 else 0,
            'warning_rate': round(warning_count / total_lines, 6) if total_lines > 0 else 0,
            'level_distribution': dict(level_counter),
            'top_components': dict(component_counter.most_common(10))
        }


# 导出插件类以供发现
plugin_class = LogParserPlugin