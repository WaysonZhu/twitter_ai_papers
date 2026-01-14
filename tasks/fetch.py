"""
增量抓取任务入口
手动执行: python -m tasks.fetch
"""
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_config import configure_root_logger
from services.fetch_service import fetch_service

# 配置日志（同时输出到控制台和文件）
configure_root_logger()


def main():
    """执行增量抓取"""
    fetch_service.run()


if __name__ == "__main__":
    main()
