"""
插件管理器，用于发现、加载和管理插件。
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Optional, Any

from plugins.base import BasePlugin, AnalysisResult


class PluginManager:
    """管理插件的发现、加载和执行。"""

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_dirs = plugin_dirs

        if self._plugin_dirs is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self._plugin_dirs = [
                os.path.join(root_dir, 'plugins', 'builtin'),
                os.path.join(root_dir, 'custom_plugins')
            ]

    def load_plugins(self) -> int:
        """扫描并加载所有插件。"""
        loaded_count = 0
        for plugin_dir in self._plugin_dirs:
            if os.path.exists(plugin_dir):
                loaded_count += self.scan_directory(plugin_dir)
        return loaded_count

    def scan_directory(self, directory: str, plugin_type: str = None) -> int:
        """扫描目录发现插件，支持递归扫描分类子目录。"""
        loaded_count = 0
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # 检查是否是分类目录（CloudBMC、iBMC、LxBMC）
                if item in ['CloudBMC', 'iBMC', 'LxBMC']:
                    loaded_count += self.scan_directory(item_path, plugin_type=item)
                else:
                    # 普通插件目录
                    plugin = self.load_plugin(item_path, plugin_type)
                    if plugin:
                        self._plugins[plugin.id] = plugin
                        loaded_count += 1
        return loaded_count

    def load_plugin(self, plugin_path: str, plugin_type: str = None) -> Optional[BasePlugin]:
        """从目录加载插件，从 plugin.json 读取元数据。"""
        plugin_file = os.path.join(plugin_path, 'plugin.py')
        if not os.path.exists(plugin_file):
            return None

        try:
            # 加载 plugin.py
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
                if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                    plugin_class = obj
                    break

            if plugin_class is None:
                return None

            plugin = plugin_class()

            # 读取 plugin.json 元数据
            json_file = os.path.join(plugin_path, 'plugin.json')
            json_metadata = {}
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_metadata = json.load(f)
                except Exception as e:
                    print(f"读取 plugin.json 失败 {json_file}: {e}")

            # 设置元数据：优先使用 json 中的值，其次是代码定义的默认值，最后是目录扫描的类型
            plugin.set_metadata(
                id=json_metadata.get('id'),
                name=json_metadata.get('name'),
                plugin_type=json_metadata.get('plugin_type') or plugin_type,
                version=json_metadata.get('version'),
                description=json_metadata.get('description')
            )

            return plugin

        except Exception as e:
            print(f"加载插件失败 {plugin_path}: {e}")
            return None

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """通过 ID 获取插件。"""
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> List[BasePlugin]:
        """获取所有已加载的插件。"""
        return list(self._plugins.values())

    def get_plugins_info(self) -> List[Dict[str, Any]]:
        """获取所有插件的信息列表。"""
        return [
            {
                'id': p.id,
                'name': p.name,
                'plugin_type': p.get_plugin_type(),
                'version': p.get_version(),
                'chinese_description': p.get_chinese_description()
            }
            for p in self._plugins.values()
        ]

    def get_plugins_categories(self) -> Dict[str, Any]:
        """获取按类型分类的插件列表。"""
        categories = {
            'CloudBMC': {'plugins': []},
            'iBMC': {'plugins': []},
            'LxBMC': {'plugins': []}
        }
        for p in self._plugins.values():
            plugin_type = p.get_plugin_type()
            if plugin_type in categories:
                categories[plugin_type]['plugins'].append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.get_chinese_description(),
                    'version': p.get_version()
                })
            else:
                # 未分类的插件放入 LxBMC
                categories['LxBMC']['plugins'].append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.get_chinese_description(),
                    'version': p.get_version()
                })
        return categories

    def get_plugins_ai_description(self) -> str:
        """获取所有插件的 AI 描述文本，用于智能选择。"""
        descriptions = []
        for p in self._plugins.values():
            desc = f"- ID: {p.id}\n"
            desc += f"  名称: {p.name}\n"
            desc += f"  类型: {p.get_plugin_type()}\n"
            desc += f"  描述: {p.get_chinese_description()}\n"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def run_analysis(self, plugin_ids: List[str], log_file: str,
                     log_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        使用指定插件运行分析。

        Args:
            plugin_ids: 要运行的插件 ID 列表
            log_file: 要分析的日志文件路径
            log_callback: 可选的日志回调函数

        Returns:
            合并后的结果字典
        """
        if not plugin_ids:
            raise ValueError("未指定要分析的插件")

        results = []
        for plugin_id in plugin_ids:
            plugin = self.get_plugin(plugin_id)
            if plugin:
                # 设置日志回调
                if log_callback:
                    plugin.set_log_callback(log_callback)
                try:
                    result = plugin.analyze(log_file)
                    results.append(result)
                except Exception as e:
                    print(f"运行插件 {plugin_id} 时出错: {e}")

        if not results:
            raise RuntimeError("没有插件成功执行")

        return self.combine_results(results)

    def run_analysis_multiple_files(self, plugin_ids: List[str], log_files: List[str],
                                     log_callback: Optional[callable] = None) -> Dict[str, Any]:
        """使用指定插件分析多个日志文件。"""
        all_results = []
        for log_file in log_files:
            for plugin_id in plugin_ids:
                plugin = self.get_plugin(plugin_id)
                if plugin:
                    if log_callback:
                        plugin.set_log_callback(log_callback)
                    try:
                        result = plugin.analyze(log_file)
                        all_results.append(result)
                    except Exception as e:
                        print(f"在 {log_file} 上运行插件 {plugin_id} 时出错: {e}")

        if not all_results:
            raise RuntimeError("没有插件成功执行")

        return self.combine_results(all_results)

    def combine_results(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """合并多个分析结果，按插件 ID 区分。"""
        if not results:
            return {}

        output = {}
        for result in results:
            plugin_id = result.meta.plugin_id
            output[plugin_id] = {
                'meta': result.meta.to_dict(),
                'sections': [s.to_dict() for s in result.sections]
            }
        return output

    def cleanup(self) -> None:
        """清理所有插件资源。"""
        self._plugins.clear()


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(custom_dirs: Optional[List[str]] = None) -> PluginManager:
    """获取全局插件管理器实例。"""
    global _plugin_manager
    if _plugin_manager is None:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        builtin_dir = os.path.join(root_dir, 'builtin')
        plugin_dirs = [builtin_dir]
        if custom_dirs:
            plugin_dirs.extend(custom_dirs)
        _plugin_manager = PluginManager(plugin_dirs=plugin_dirs)
        count = _plugin_manager.load_plugins()
        print(f"已加载 {count} 个插件")
    return _plugin_manager


def reset_plugin_manager() -> None:
    """重置全局插件管理器。"""
    global _plugin_manager
    if _plugin_manager:
        _plugin_manager.cleanup()
    _plugin_manager = None