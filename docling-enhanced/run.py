#!/usr/bin/env python3
"""
Docling Enhanced - 启动脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """主启动函数"""
    print("🚀 启动 Docling Enhanced...")
    
    # 检查当前目录
    current_dir = Path(__file__).parent
    ui_file = current_dir / "docling_ui.py"
    
    if not ui_file.exists():
        print("❌ 错误: 找不到 docling_ui.py 文件")
        print(f"请确保在正确的目录中运行: {current_dir}")
        sys.exit(1)
    
    # 检查依赖
    try:
        import streamlit
        import docling
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 启动Streamlit
    try:
        print("🌐 启动Web界面...")
        print("📍 访问地址: http://localhost:8501")
        print("⏹️  按 Ctrl+C 停止服务")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(ui_file),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()