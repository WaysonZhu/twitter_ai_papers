"""
日志配置模块
同时输出到控制台和文件
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config.settings import settings


def setup_logging(name: str = None) -> logging.Logger:
    """
    配置日志，同时输出到控制台和文件

    Args:
        name: logger 名称，默认为 root logger

    Returns:
        配置好的 logger 实例
    """
    # 获取 logger
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 控制台处理器（始终添加）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. 文件处理器（如果配置了 LOG_DIR）
    if settings.LOG_DIR:
        try:
            # 确保日志目录存在
            log_dir = settings.LOG_DIR
            os.makedirs(log_dir, exist_ok=True)

            # 日志文件名：按日期命名
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(log_dir, f'ai_papers_{today}.log')

            # 使用 RotatingFileHandler，单个文件最大 10MB，保留 7 个备份
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=7,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            logger.info(f"日志文件: {log_file}")

        except Exception as e:
            logger.warning(f"无法创建日志文件: {e}")

    return logger


def configure_root_logger():
    """
    配置 root logger，让所有模块的日志都使用相同的配置
    """
    # 获取 root logger
    root_logger = logging.getLogger()

    # 如果已经配置过，先清除
    root_logger.handlers.clear()

    # 设置日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. 文件处理器
    if settings.LOG_DIR:
        try:
            log_dir = settings.LOG_DIR
            os.makedirs(log_dir, exist_ok=True)

            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(log_dir, f'ai_papers_{today}.log')

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=7,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            root_logger.info(f"日志输出到文件: {log_file}")

        except Exception as e:
            root_logger.warning(f"无法创建日志文件: {e}")

    return root_logger
