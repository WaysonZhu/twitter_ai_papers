"""
抓取器基类
提供通用的抓取逻辑
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

from utils.http_client import HttpClient, HttpxClient

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """抓取器基类"""

    def __init__(self):
        self.http_client = HttpClient()
        self.httpx_client = HttpxClient()

    @abstractmethod
    def fetch(self, identifier: str) -> Optional[Any]:
        """
        抓取数据

        Args:
            identifier: 标识符（如 arxiv_id, github_url 等）

        Returns:
            抓取到的数据，失败返回 None
        """
        pass

    def _log_success(self, source: str, identifier: str):
        """记录成功日志"""
        logger.info(f"[{source}] 成功获取: {identifier}")

    def _log_error(self, source: str, identifier: str, error: str):
        """记录错误日志"""
        logger.error(f"[{source}] 获取失败 {identifier}: {error}")

    def _log_not_found(self, source: str, identifier: str):
        """记录未找到日志"""
        logger.warning(f"[{source}] 未找到: {identifier}")
