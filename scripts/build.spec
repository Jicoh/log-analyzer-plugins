# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件
编译插件系统为单文件可执行文件
"""

import os
import shutil
import tempfile
import atexit
from PyInstaller.utils.hooks import collect_submodules

# 获取目录路径
scripts_dir = os.path.dirname(os.path.abspath(SPEC))
plugins_dir = os.path.dirname(scripts_dir)

# 创建临时目录结构，确保plugins包可被PyInstaller发现
# 独立仓库目录名可能不是plugins，PyInstaller需要名为plugins的子目录
_build_tmp = tempfile.mkdtemp(prefix='plugin_build_')
_plugins_tmp = os.path.join(_build_tmp, 'plugins')
shutil.copytree(plugins_dir, _plugins_tmp,
                ignore=shutil.ignore_patterns('tests', 'scripts', 'hooks',
                                               '__pycache__', 'dist', 'build', '.git'))
atexit.register(lambda: shutil.rmtree(_build_tmp, ignore_errors=True))

# 收集数据文件
datas = [
    (os.path.join(_plugins_tmp, 'renderer', 'template.html'), 'plugins/renderer'),
    (os.path.join(_plugins_tmp, 'renderer', 'batch_template.html'), 'plugins/renderer'),
    (os.path.join(_plugins_tmp, 'builtin'), 'plugins/builtin'),
]

# 隐式导入
hiddenimports = [
    'plugins',
    'plugins.base',
    'plugins.manager',
    'plugins.renderer',
    'plugins.renderer.html_renderer',
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',
    'jinja2',
    'jinja2.ext',
    'dateutil',
    'dateutil.parser',
    'chardet',
]

# 收集 pandas 和 jinja2 的子模块
hiddenimports.extend(collect_submodules('pandas'))
hiddenimports.extend(collect_submodules('jinja2'))

a = Analysis(
    [os.path.join(plugins_dir, 'cli_main.py')],
    pathex=[_build_tmp],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(plugins_dir, 'hooks', 'runtime_hook.py')],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='log-analyzer-plugin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
