# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - Docling UI 应用
用于打包 Streamlit 可视化界面为独立可执行文件
"""

import sys
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

# 数据文件和隐藏导入
datas = [
    # Streamlit 静态文件
    (str(project_root / "docling_ui.py"), "."),
    (str(project_root / "requirements_ui.txt"), "."),
]

# 隐藏导入 - 包含所有必要的模块
hiddenimports = [
    # Streamlit 核心
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.script_runner',
    'streamlit.runtime.state',
    'streamlit.components.v1',
    
    # Docling 核心模块
    'docling',
    'docling.document_converter',
    'docling.datamodel.base_models',
    'docling.datamodel.pipeline_options',
    'docling.datamodel.backend_options',
    'docling_core',
    'docling_parse',
    'docling_ibm_models',
    
    # 数据处理
    'pandas',
    'numpy',
    'PIL',
    'PIL.Image',
    
    # 其他依赖
    'queue',
    'logging',
    'tempfile',
    'zipfile',
    'base64',
    'io',
    're',
    'traceback',
    
    # 可能的隐藏依赖
    'altair',
    'plotly',
    'matplotlib',
    'seaborn',
]

# 排除的模块
excludes = [
    'tkinter',
    'matplotlib.backends._backend_tk',
]

# 分析配置
a = Analysis(
    ['run_ui.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 处理重复文件
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='docling-ui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保持控制台以显示 Streamlit 输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

# macOS 应用包配置（仅在 macOS 上）
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Docling-UI.app',
        icon=None,  # 可以添加 .icns 图标文件
        bundle_identifier='com.docling.ui',
        info_plist={
            'CFBundleName': 'Docling UI',
            'CFBundleDisplayName': 'Docling 文档转换器',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
        },
    )