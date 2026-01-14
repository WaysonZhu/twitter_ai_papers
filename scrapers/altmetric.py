"""
Altmetric 社交传播指标抓取器
从 Altmetric API 获取社交传播数据
"""
import logging
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AltmetricScraper(BaseScraper):
    """Altmetric 社交传播指标抓取器"""

    BASE_URL = "https://api.altmetric.com/v1"

    def fetch(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Altmetric 社交传播数据

        Args:
            arxiv_id: ArXiv 论文 ID

        Returns:
            包含 x_num (Twitter提及), cited_by_msm_count (媒体引用) 等的字典
        """
        if not arxiv_id:
            return None

        url = f"{self.BASE_URL}/arxiv/{arxiv_id}"
        logger.info(f"[Altmetric] 获取: {arxiv_id}")

        try:
            response = self.httpx_client.get(url)

            if not response:
                self._log_error("Altmetric", arxiv_id, "请求失败")
                return None

            if response.status_code == 404:
                self._log_not_found("Altmetric", arxiv_id)
                return None

            if response.status_code != 200:
                self._log_error("Altmetric", arxiv_id, f"状态码: {response.status_code}")
                return None

            data = response.json()

            result = {
                'x_num': data.get('cited_by_tweeters_count', 0) or 0,
                'cited_by_msm_count': data.get('cited_by_msm_count', 0) or 0,
                'altmetric_score': data.get('score', 0.0) or 0.0,
                'title': data.get('title', ''),
                'journal': data.get('journal', ''),
                'type': data.get('type', ''),
            }

            self._log_success("Altmetric", arxiv_id)
            return result

        except Exception as e:
            self._log_error("Altmetric", arxiv_id, str(e))
            return None
