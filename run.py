#!/usr/bin/env python3
"""
一键启动脚本
"""
import sys
from pathlib import Path

# 将 src 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app import create_app
from config import Config

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=False)
