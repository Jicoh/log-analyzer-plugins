"""
插件系统 PyInstaller 运行时钩子
在exe启动时执行，设置正确的模块搜索路径
"""

import sys
import os

if getattr(sys, 'frozen', False):
    # exe运行时，添加exe所在目录到sys.path（用于加载外部自定义插件）
    exe_dir = os.path.dirname(sys.executable)
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

    # 添加内部资源路径到sys.path
    meipass = sys._MEIPASS
    if meipass not in sys.path:
        sys.path.insert(0, meipass)
