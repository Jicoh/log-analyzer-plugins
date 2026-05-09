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

    # 确保plugins包可导入（PyInstaller打包后可能缺少正确的包结构）
    if 'plugins' not in sys.modules:
        try:
            import plugins
        except ImportError:
            import importlib.util
            plugins_dir = os.path.join(meipass, 'plugins')
            init_path = os.path.join(plugins_dir, '__init__.py')
            if os.path.exists(init_path):
                spec = importlib.util.spec_from_file_location(
                    'plugins', init_path,
                    submodule_search_locations=[plugins_dir]
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules['plugins'] = module
                spec.loader.exec_module(module)
