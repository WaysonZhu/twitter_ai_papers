"""
ArXiv 论文信息抓取器
从 arXiv 网站获取论文的详细信息
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ArxivScraper(BaseScraper):
    """ArXiv 论文信息抓取器"""

    BASE_URL = "https://arxiv.org/abs/"

    def fetch(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 ArXiv 论文信息

        Args:
            arxiv_id: ArXiv 论文 ID，如 2501.12345

        Returns:
            论文信息字典，包含 title, authors, pub_date, url
        """
        if not arxiv_id:
            return None

        url = f"{self.BASE_URL}{arxiv_id}"

        try:
            logger.info(f"[ArXiv] 获取: {arxiv_id}")
            response = self.http_client.get(url)

            if not response:
                self._log_error("ArXiv", arxiv_id, "请求失败")
                return None

            if response.status_code == 404:
                self._log_not_found("ArXiv", arxiv_id)
                return None

            if response.status_code != 200:
                self._log_error("ArXiv", arxiv_id, f"状态码: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title_tag = soup.find('h1', class_='title mathjax')
            title = ""
            if title_tag:
                title = title_tag.get_text(strip=True).replace('Title:', '').strip()

            # 提取作者
            authors_tag = soup.find('div', class_='authors')
            authors = ""
            if authors_tag:
                author_links = authors_tag.find_all('a')
                authors = ', '.join([a.get_text(strip=True) for a in author_links])

            # 提取日期
            pub_date = None
            date_tag = soup.find('div', class_='dateline')
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                pub_date = self._parse_date(date_text)

            result = {
                'title': title,
                'authors': authors,
                'pub_date': pub_date,
                'arxiv_id': arxiv_id,
                'url': url,
            }

            self._log_success("ArXiv", arxiv_id)
            return result

        except Exception as e:
            self._log_error("ArXiv", arxiv_id, str(e))
            return None

    def _parse_date(self, date_text: str) -> Optional[str]:
        """解析日期文本"""
        try:
            # 处理 "last revised" 格式
            if 'last revised' in date_text:
                raw_date_part = date_text.split('last revised')[-1].strip()
            else:
                raw_date_part = date_text.split("on")[-1].strip().rstrip(']')

            # 去除括号等多余内容
            raw_date = raw_date_part.split('(')[0].strip()

            # 解析日期格式如 "17 Jun 2025"
            parsed_date = datetime.strptime(raw_date, "%d %b %Y")
            return parsed_date.strftime("%Y-%m-%d")

        except ValueError:
            return None
