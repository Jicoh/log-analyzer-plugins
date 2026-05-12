#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件系统独立CLI入口

用法:
    python plugins/cli_main.py plugin list
    echo '{"日志1": "内容"}' | python plugins/cli_main.py analyze --plugin-id CloudBMC_00001
"""

import sys
import os
import json
import argparse
import importlib.util

# 确保plugins包可被导入
if not getattr(sys, 'frozen', False):
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(cli_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # 独立仓库运行时，当前目录可能不在名为plugins的父目录下
    # 检测并注册当前目录为plugins包
    try:
        import plugins
    except ImportError:
        init_path = os.path.join(cli_dir, '__init__.py')
        spec = importlib.util.spec_from_file_location(
            'plugins', init_path,
            submodule_search_locations=[cli_dir]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules['plugins'] = module
        spec.loader.exec_module(module)

from plugins.manager import PluginManager


def cmd_plugin_list(manager):
    """显示插件列表"""
    plugins = manager.get_all_plugins()
    if not plugins:
        print("暂无可用插件")
        return 0
    for plugin in plugins:
        plugin_type = plugin.get_plugin_type()
        print(f"[{plugin_type}] {plugin.name}({plugin.id}): {plugin.get_chinese_description()} (v{plugin.get_version()})")
    return 0


def cmd_analyze(manager, args):
    """执行分析"""
    # 从stdin读取日志内容JSON
    try:
        input_data = sys.stdin.read()
        log_content = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"错误: 日志内容JSON解析失败: {e}", file=sys.stderr)
        return 1

    if not isinstance(log_content, dict):
        print("错误: 日志内容必须是字典格式", file=sys.stderr)
        return 1

    result = manager.run_analysis(
        source='cli',
        plugin_ids=[args.plugin_id],
        log_content=log_content,
        task_name=args.task_name or "",
        bmc_ip=args.bmc_ip or "",
        date=args.date or ""
    )
    print(result)
    return 0


def main():
    parser = argparse.ArgumentParser(description='日志分析插件工具')
    subparsers = parser.add_subparsers(dest='command')

    # plugin list
    plugin_parser = subparsers.add_parser('plugin', help='插件管理')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action', help='插件操作')
    plugin_subparsers.add_parser('list', help='列出可用插件')

    # analyze
    analyze_parser = subparsers.add_parser('analyze', help='执行日志分析')
    analyze_parser.add_argument('--plugin-id', required=True, help='插件ID')
    analyze_parser.add_argument('--task-name', default='', help='任务名称')
    analyze_parser.add_argument('--bmc-ip', default='', help='BMC IP地址')
    analyze_parser.add_argument('--date', default='', help='日期')

    args = parser.parse_args()

    # 初始化插件管理器
    manager = PluginManager()
    manager.load_plugins()

    if args.command == 'plugin' and args.plugin_action == 'list':
        return cmd_plugin_list(manager)
    elif args.command == 'analyze':
        return cmd_analyze(manager, args)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
