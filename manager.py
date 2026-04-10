"""
插件管理器，用于发现、加载和管理插件。

本模块提供 PluginManager 类，负责：
- 在内置和自定义目录中发现插件
- 动态加载插件
- 执行插件并聚合结果
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Optional, Any
from datetime import datetime

from plugins.base import BasePlugin, PluginCategory, PluginInfo, AnalysisResult, MultiPluginAnalysisResult


class PluginManager:
    """
    管理插件的发现、加载和执行。

    PluginManager 扫描配置的目录以发现插件，
    动态加载它们，并提供查询和执行插件的方法。
    """

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        初始化 PluginManager。

        Args:
            plugin_dirs: 可选的插件扫描目录列表。
                        如果为 None，则使用默认目录（内置和自定义）。
        """
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_dirs = plugin_dirs

        if self._plugin_dirs is None:
            # 默认插件目录
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self._plugin_dirs = [
                os.path.join(root_dir, 'plugins', 'builtin'),
                os.path.join(root_dir, 'plugins', 'custom')
            ]

    def load_plugins(self) -> int:
        """
        扫描插件目录并加载所有有效插件。

        Returns:
            成功加载的插件数量。
        """
        loaded_count = 0

        for plugin_dir in self._plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue

            loaded_count += self.scan_directory(plugin_dir)

        return loaded_count

    def scan_directory(self, directory: str) -> int:
        """
        扫描目录以发现插件。

        Args:
            directory: 要扫描的目录。

        Returns:
            从该目录加载的插件数量。
        """
        loaded_count = 0

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            # 检查是否为可能的插件目录
            if os.path.isdir(item_path):
                plugin = self.load_plugin(item_path)
                if plugin:
                    self._plugins[plugin.id] = plugin
                    loaded_count += 1

        return loaded_count

    def load_plugin(self, plugin_path: str) -> Optional[BasePlugin]:
        """
        从目录加载插件。

        Args:
            plugin_path: 插件目录路径。

        Returns:
            加载的插件实例，如果加载失败则返回 None。
        """
        plugin_file = os.path.join(plugin_path, 'plugin.py')
        metadata_file = os.path.join(plugin_path, 'plugin.json')

        # 检查必需的 plugin.py 文件是否存在
        if not os.path.exists(plugin_file):
            return None

        try:
            # 加载插件模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{os.path.basename(plugin_path)}",
                plugin_file
            )
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and
                    issubclass(obj, BasePlugin) and
                    obj is not BasePlugin):
                    plugin_class = obj
                    break

            if plugin_class is None:
                return None

            # 实例化插件
            plugin = plugin_class()

            # 如果有元数据文件则加载
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    # 元数据可以在需要时覆盖插件属性
                    plugin._metadata = metadata
                except (json.JSONDecodeError, IOError):
                    pass

            # 初始化插件
            plugin.initialize()

            return plugin

        except Exception as e:
            print(f"加载插件失败 {plugin_path}: {e}")
            return None

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """
        通过 ID 获取插件。

        Args:
            plugin_id: 插件的唯一标识符。

        Returns:
            插件实例，如果未找到则返回 None。
        """
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[BasePlugin]:
        """
        获取所有已加载的插件。

        Returns:
            所有已加载插件实例的列表。
        """
        return list(self._plugins.values())

    def get_plugins_info(self) -> List[PluginInfo]:
        """
        获取所有已加载插件的信息。

        Returns:
            PluginInfo 对象列表。
        """
        return [plugin.get_info() for plugin in self._plugins.values()]

    def get_plugins_by_category(self, category: PluginCategory) -> List[BasePlugin]:
        """
        按类别筛选插件。

        Args:
            category: 要筛选的类别。

        Returns:
            指定类别中的插件列表。
        """
        return [p for p in self._plugins.values() if p.category == category]

    def get_plugins_by_category_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        按类别分组获取插件。

        Returns:
            将类别名称映射到插件列表的字典。
        """
        categories = {}
        for plugin in self._plugins.values():
            cat_value = plugin.category.value
            if cat_value not in categories:
                categories[cat_value] = {
                    'label': plugin.category.name,
                    'plugins': []
                }
            categories[cat_value]['plugins'].append(plugin.get_info().to_dict())
        return categories

    def get_plugins_ai_description(self) -> str:
        """
        获取所有插件的 AI 可读描述。

        Returns:
            str: AI 可读的插件描述文本
        """
        descriptions = []
        for plugin in self._plugins.values():
            descriptions.append(plugin.get_ai_description())
        return "\n---\n".join(descriptions)

    def run_analysis(self, plugin_ids: List[str], log_file: str) -> MultiPluginAnalysisResult:
        """
        使用指定的插件运行分析。

        Args:
            plugin_ids: 要运行的插件 ID 列表。
            log_file: 要分析的日志文件路径。

        Returns:
            包含每个插件结果的 MultiPluginAnalysisResult。
        """
        if not plugin_ids:
            raise ValueError("未指定要分析的插件")

        results = []
        for plugin_id in plugin_ids:
            plugin = self.get_plugin(plugin_id)
            if plugin:
                try:
                    result = plugin.analyze(log_file)
                    results.append(result)
                except Exception as e:
                    print(f"运行插件 {plugin_id} 时出错: {e}")

        if not results:
            raise RuntimeError("没有插件成功执行")

        # 将结果合并为多插件结构
        return self.combine_results(results)

    def run_analysis_multiple_files(
        self,
        plugin_ids: List[str],
        log_files: List[str]
    ) -> MultiPluginAnalysisResult:
        """
        使用指定的插件分析多个日志文件。

        Args:
            plugin_ids: 要运行的插件 ID 列表。
            log_files: 要分析的日志文件路径列表。

        Returns:
            包含每个插件结果的 MultiPluginAnalysisResult。
        """
        all_results = []

        for log_file in log_files:
            for plugin_id in plugin_ids:
                plugin = self.get_plugin(plugin_id)
                if plugin:
                    try:
                        result = plugin.analyze(log_file)
                        all_results.append(result)
                    except Exception as e:
                        print(f"在 {log_file} 上运行插件 {plugin_id} 时出错: {e}")

        if not all_results:
            raise RuntimeError("没有插件成功执行")

        return self.combine_results(all_results)

    def combine_results(self, results: List[AnalysisResult]) -> MultiPluginAnalysisResult:
        """
        将多个分析结果合并为 MultiPluginAnalysisResult。

        结果按插件 ID 存储，保留每个插件的结构。
        当同一插件分析多个文件时，其结果会被合并。

        Args:
            results: 要合并的 AnalysisResult 对象列表。

        Returns:
            具有按插件结构的 MultiPluginAnalysisResult。
        """
        if not results:
            return MultiPluginAnalysisResult(
                analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                log_file='none'
            )

        multi_result = MultiPluginAnalysisResult(
            analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            log_file=', '.join(set(r.log_file for r in results))
        )

        # 按插件 ID 分组结果
        for result in results:
            plugin_id = result.plugin_id
            if plugin_id in multi_result.plugins:
                # 与同一插件的现有结果合并
                existing = multi_result.plugins[plugin_id]
                existing.error_count += result.error_count
                existing.warning_count += result.warning_count
                existing.errors.extend(result.errors)
                existing.warnings.extend(result.warnings)
                # 合并统计数据
                for key, value in result.statistics.items():
                    if key in existing.statistics:
                        if isinstance(value, (int, float)) and isinstance(existing.statistics[key], (int, float)):
                            existing.statistics[key] += value
                        elif isinstance(value, dict) and isinstance(existing.statistics[key], dict):
                            existing.statistics[key].update(value)
                    else:
                        existing.statistics[key] = value
                # 如果两者都是字典则合并 raw_output
                if isinstance(result.raw_output, dict) and isinstance(existing.raw_output, dict):
                    existing.raw_output.update(result.raw_output)
            else:
                # 为此插件创建新条目
                multi_result.plugins[plugin_id] = result

        return multi_result

    def cleanup(self) -> None:
        """清理所有已加载的插件。"""
        for plugin in self._plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"清理插件 {plugin.id} 时出错: {e}")
        self._plugins.clear()


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(custom_dirs: Optional[List[str]] = None) -> PluginManager:
    """
    获取全局插件管理器实例。

    如果不存在则创建管理器并加载插件。

    Args:
        custom_dirs: 可选的外部自定义插件目录列表。

    Returns:
        全局 PluginManager 实例。
    """
    global _plugin_manager
    if _plugin_manager is None:
        # builtin目录(子模块内)
        root_dir = os.path.dirname(os.path.abspath(__file__))
        builtin_dir = os.path.join(root_dir, 'builtin')

        # 合并目录: builtin + custom
        plugin_dirs = [builtin_dir]
        if custom_dirs:
            plugin_dirs.extend(custom_dirs)

        _plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
        count = _plugin_manager.load_plugins()
        print(f"已加载 {count} 个插件")
    return _plugin_manager


def reset_plugin_manager() -> None:
    """
    重置全局插件管理器。

    适用于测试或重新加载插件。
    """
    global _plugin_manager
    if _plugin_manager:
        _plugin_manager.cleanup()
    _plugin_manager = None