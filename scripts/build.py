#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编译插件系统为单文件可执行文件

用法:
    cd plugins
    python scripts/build.py
"""

import os
import sys
import subprocess


def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def main():
    # 切换到 plugins 目录
    plugins_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(plugins_dir)
    print(f"工作目录: {plugins_dir}")

    # 检查 PyInstaller
    if not check_pyinstaller():
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return 1

    # 检查 spec 文件
    spec_file = os.path.join(plugins_dir, 'scripts', 'build.spec')
    if not os.path.exists(spec_file):
        print(f"错误: 找不到 spec 文件: {spec_file}")
        return 1

    # 执行编译
    print("开始编译...")
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', spec_file]
    result = subprocess.run(cmd, cwd=plugins_dir)

    if result.returncode == 0:
        print("\n编译成功!")
        if sys.platform == 'win32':
            exe_path = os.path.join(plugins_dir, 'dist', 'log-analyzer-plugin.exe')
        else:
            exe_path = os.path.join(plugins_dir, 'dist', 'log-analyzer-plugin')
        print(f"输出文件: {exe_path}")
        return 0
    else:
        print("\n编译失败!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
