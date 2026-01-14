"""
HuggingFace Trending 论文抓取器
抓取 https://huggingface.co/papers/trending + 当天日期页面
"""
import re
import logging
from typing import List, Optional, Set
from datetime import datetime, date

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from models.paper import Paper

logger = logging.getLogger(__name__)


class HFTrendingScraper(BaseScraper):
    """HuggingFace Trending 论文抓取器"""

    TRENDING_URL = "https://huggingface.co/papers/trending"
    DATE_URL_TEMPLATE = "https://huggingface.co/papers/date/{date}"

    def fetch(self, identifier: str = None) -> List[Paper]:
        """
        抓取 HuggingFace 论文列表
        1. 先抓取 Trending 页面（热门论文）
        2. 再抓取当天日期页面（确保不遗漏新论文）
        3. 合并去重后返回

        Returns:
            论文列表
        """
        all_paper_links: Set[str] = set()
        papers = []

        # 1. 抓取 Trending 页面
        trending_links = self._fetch_paper_links(self.TRENDING_URL, "Trending")
        all_paper_links.update(trending_links)

        # 2. 抓取当天日期页面
        today = date.today().strftime('%Y-%m-%d')
        date_url = self.DATE_URL_TEMPLATE.format(date=today)
        date_links = self._fetch_paper_links(date_url, f"Date({today})")
        all_paper_links.update(date_links)

        logger.info(f"合并去重后共 {len(all_paper_links)} 篇论文链接")

        # 3. 抓取每篇论文详情
        paper_links = list(all_paper_links)
        for i, link in enumerate(paper_links):
            paper = self._fetch_paper_detail(link, i + 1, len(paper_links))
            if paper:
                papers.append(paper)

        logger.info(f"成功抓取 {len(papers)} 篇论文")
        return papers

    def _fetch_paper_links(self, url: str, source_name: str) -> Set[str]:
        """
        从指定页面抓取论文链接

        Args:
            url: 页面 URL
            source_name: 来源名称（用于日志）

        Returns:
            论文链接集合
        """
        paper_links = set()

        try:
            logger.info(f"正在抓取 {source_name}: {url}")
            response = self.http_client.get(url)

            if not response or response.status_code != 200:
                self._log_error("HF", url, f"状态码: {response.status_code if response else 'None'}")
                return paper_links

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')

            for article in articles:
                article_link = article.find('a')
                if article_link and 'href' in article_link.attrs:
                    href = article_link['href']
                    # 只保留论文链接（以 /papers/ 开头且包含 arxiv_id）
                    if href.startswith('/papers/') and re.search(r'/papers/\d+\.\d+', href):
                        paper_links.add(f"https://huggingface.co{href}")

            logger.info(f"{source_name} 找到 {len(paper_links)} 篇论文链接")
            return paper_links

        except Exception as e:
            self._log_error("HF", url, str(e))
            return paper_links

    def _fetch_paper_detail(self, url: str, index: int, total: int) -> Optional[Paper]:
        """抓取单篇论文详情"""
        try:
            logger.debug(f"[{index}/{total}] 抓取: {url}")

            response = self.http_client.get(url)
            if not response or response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title_element = soup.find('h1')
            title = title_element.text.strip() if title_element else ""

            # 提取作者
            authors = ""
            authors_element = soup.find(string=re.compile(r'Authors:'))
            if authors_element:
                authors_parent = authors_element.find_parent()
                if authors_parent:
                    authors_parent = authors_parent.find_parent()
                if authors_parent:
                    authors_text = authors_parent.get_text(strip=True)
                    authors_match = re.search(r'Authors:(.*)', authors_text)
                    if authors_match:
                        authors = authors_match.group(1).strip()

            # 提取摘要
            abstract = ""
            abstract_element = soup.find(string=re.compile(r'Abstract'))
            if abstract_element:
                abstract_parent = abstract_element.find_parent()
                if abstract_parent:
                    next_p = abstract_parent.find_next('p')
                    if next_p:
                        abstract = next_p.text.strip()

            # 查找 PDF 链接和 arxiv_id
            pdf_link_element = soup.find('a', href=re.compile(r'^https://arxiv.org/pdf/.*'))
            pdf_url = pdf_link_element['href'] if pdf_link_element else ""

            arxiv_id = ""
            if pdf_url:
                # 从 PDF URL 提取 arxiv_id，如 2501.12345
                match = re.search(r'/(\d+\.\d+)', pdf_url)
                if match:
                    arxiv_id = match.group(1)

            # 查找 GitHub 链接
            github_link_element = soup.find('a', href=re.compile(r'^https://github.com/[^/]+/[^/]+'))
            github_url = github_link_element['href'] if github_link_element else None

            if not arxiv_id:
                logger.warning(f"无法从 {url} 提取 arxiv_id")
                return None

            return Paper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                github_url=github_url,
                from_source="HF_TRENDING",
            )

        except Exception as e:
            logger.error(f"抓取论文详情失败 {url}: {e}")
            return None
