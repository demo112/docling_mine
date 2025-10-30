#!/usr/bin/env python3
"""
Docling 可视化界面启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import streamlit
        import pandas
        from PIL import Image
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return False


def install_dependencies():
    """安装依赖"""
    print("正在安装可视化界面依赖...")
    requirements_file = Path(__file__).parent / "requirements_ui.txt"
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 启动 Docling 可视化界面...")
    
    # 检查依赖
    if not check_dependencies():
        print("正在安装缺少的依赖...")
        if not install_dependencies():
            print("❌ 无法安装依赖，请手动运行: pip install -r requirements_ui.txt")
            return
    
    # 启动 Streamlit 应用
    ui_file = Path(__file__).parent / "docling_ui.py"
    
    try:
        print(f"📄 启动界面文件: {ui_file}")
        print("🌐 浏览器将自动打开，如果没有请访问: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止服务")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(ui_file),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 已停止 Docling 可视化界面")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


if __name__ == "__main__":
    main()