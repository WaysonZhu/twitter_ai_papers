"""
Mendeley 阅读数抓取器
从 Mendeley API 获取论文阅读数据
"""
import time
import logging
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper
from config.settings import settings

logger = logging.getLogger(__name__)


class MendeleyScraper(BaseScraper):
    """Mendeley 阅读数抓取器"""

    TOKEN_URL = "https://api.mendeley.com/oauth/token"
    CATALOG_URL = "https://api.mendeley.com/catalog"

    def __init__(self):
        super().__init__()
        self._token = None

    def _refresh_token(self) -> bool:
        """刷新 Mendeley API Token"""
        if not settings.MENDELEY_CLIENT_ID or not settings.MENDELEY_CLIENT_SECRET:
            logger.warning("[Mendeley] 未配置 Client ID 或 Secret")
            return False

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.http_client.post(
                    self.TOKEN_URL,
                    data={
                        "scope": "all",
                        "grant_type": "client_credentials",
                        "client_id": settings.MENDELEY_CLIENT_ID,
                        "client_secret": settings.MENDELEY_CLIENT_SECRET,
                    }
                )

                if response and response.status_code == 200:
                    self._token = response.json().get("access_token")
                    logger.info("[Mendeley] Token 刷新成功")
                    return True

                logger.warning(f"[Mendeley] Token 刷新失败: {response.status_code if response else 'None'}")
                time.sleep(5)

            except Exception as e:
                logger.error(f"[Mendeley] Token 刷新异常: {e}")
                time.sleep(5)

        return False

    def fetch(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Mendeley 论文数据

        Args:
            arxiv_id: ArXiv 论文 ID

        Returns:
            包含 reader_count, journal 等信息的字典
        """
        if not arxiv_id:
            return None

        logger.info(f"[Mendeley] 获取: {arxiv_id}")

        # 确保有 Token
        if not self._token:
            if not self._refresh_token():
                return None

        params = {"view": "all", "arxiv": arxiv_id}
        headers = {"Authorization": f"Bearer {self._token}"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.http_client.get(
                    self.CATALOG_URL,
                    params=params,
                    headers=headers
                )

                if not response:
                    continue

                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        item = data[0]
                        result = {
                            'reader_count': item.get('reader_count', 0),
                            'journal': item.get('source'),
                        }
                        self._log_success("Mendeley", arxiv_id)
                        return result
                    else:
                        self._log_not_found("Mendeley", arxiv_id)
                        return None

                elif response.status_code == 401:
                    # Token 过期，刷新后重试
                    logger.warning("[Mendeley] Token 过期，刷新中...")
                    if self._refresh_token():
                        headers = {"Authorization": f"Bearer {self._token}"}
                        continue
                    return None

                elif response.status_code == 404:
                    self._log_not_found("Mendeley", arxiv_id)
                    return None

                else:
                    self._log_error("Mendeley", arxiv_id, f"状态码: {response.status_code}")
                    time.sleep(2)

            except Exception as e:
                self._log_error("Mendeley", arxiv_id, str(e))
                time.sleep(2)

        return None
