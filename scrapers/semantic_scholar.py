"""
Semantic Scholar 引用数抓取器
从 Semantic Scholar API 获取论文引用数据
"""
import time
import logging
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper
from config.settings import settings

logger = logging.getLogger(__name__)


class SemanticScholarScraper(BaseScraper):
    """Semantic Scholar 引用数抓取器"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/ARXIV:"

    def fetch(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Semantic Scholar 引用数据

        Args:
            arxiv_id: ArXiv 论文 ID

        Returns:
            包含 citation_count, reference_count 等的字典
        """
        if not arxiv_id:
            return None

        fields = "title,authors,year,citationCount,referenceCount,externalIds,url"
        url = f"{self.BASE_URL}{arxiv_id}?fields={fields}"

        logger.info(f"[SemanticScholar] 获取: {arxiv_id}")

        # 构建请求头
        headers = {}
        if settings.SEMANTIC_SCHOLAR_API_KEY:
            headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self.httpx_client.get(url, headers=headers if headers else None)

                if not response:
                    time.sleep(2)
                    continue

                if response.status_code == 404:
                    self._log_not_found("SemanticScholar", arxiv_id)
                    return None

                if response.status_code == 429:
                    # 速率限制，等待后重试
                    wait_time = 10 * (attempt + 1)
                    logger.warning(f"[SemanticScholar] 速率限制，等待 {wait_time}s")
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    self._log_error("SemanticScholar", arxiv_id, f"状态码: {response.status_code}")
                    time.sleep(2)
                    continue

                data = response.json()

                result = {
                    'citation_count': data.get('citationCount', 0) or 0,
                    'reference_count': data.get('referenceCount', 0) or 0,
                    'title': data.get('title', ''),
                    'year': data.get('year'),
                    'authors': [a.get('name', '') for a in data.get('authors', [])],
                }

                self._log_success("SemanticScholar", arxiv_id)
                return result

            except Exception as e:
                self._log_error("SemanticScholar", arxiv_id, str(e))
                time.sleep(2)

        logger.error(f"[SemanticScholar] 达到最大重试次数: {arxiv_id}")
        return None
