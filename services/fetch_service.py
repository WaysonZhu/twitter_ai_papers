"""
增量抓取服务
功能1：抓取 HuggingFace Trending 新论文，增量入库
"""
import logging
from datetime import datetime

from config.settings import settings
from scrapers.hf_trending import HFTrendingScraper
from scrapers.x_trending import XTrendingScraper
from scrapers.arxiv import ArxivScraper
from scrapers.mendeley import MendeleyScraper
from scrapers.altmetric import AltmetricScraper
from scrapers.github_scraper import GitHubScraper
from scrapers.semantic_scholar import SemanticScholarScraper
from database.repository import paper_repo
from models.paper import Paper

logger = logging.getLogger(__name__)


class FetchService:
    """增量抓取服务"""

    def __init__(self):
        self.hf_scraper = HFTrendingScraper()
        self.x_scraper = XTrendingScraper()
        self.arxiv_scraper = ArxivScraper()
        self.mendeley_scraper = MendeleyScraper()
        self.altmetric_scraper = AltmetricScraper()
        self.github_scraper = GitHubScraper()
        self.semantic_scholar_scraper = SemanticScholarScraper()

    def run(self):
        """执行增量抓取"""
        logger.info("=" * 60)
        logger.info(f"[FetchService] 开始增量抓取 - {datetime.now()}")
        logger.info("=" * 60)

        # 1. 抓取 HuggingFace Trending 论文列表
        logger.info("步骤1: 抓取 HuggingFace Trending 论文列表")
        papers = self.hf_scraper.fetch()
        logger.info(f"HuggingFace Trending 抓取到 {len(papers)} 篇论文")

        # 2. 抓取 X Trending 论文列表（如果启用）
        if settings.SCRAPER_X_TRENDING_ENABLED:
            logger.info("步骤1.5: 抓取 X Trending 论文列表")
            x_papers = self.x_scraper.fetch()
            logger.info(f"X Trending 抓取到 {len(x_papers)} 篇论文")

            # 合并两个数据源（去重会在后续步骤处理）
            papers.extend(x_papers)
            logger.info(f"合并后共 {len(papers)} 篇论文")

        if not papers:
            logger.warning("没有抓取到论文")
            return

        logger.info(f"总共抓取到 {len(papers)} 篇论文")

        # 2. 过滤已存在的论文（去重）
        logger.info("步骤2: 过滤已存在的论文")
        existing_ids = paper_repo.get_existing_arxiv_ids()
        new_papers = [p for p in papers if p.arxiv_id not in existing_ids]

        if not new_papers:
            logger.info("没有新论文需要处理")
            return

        logger.info(f"发现 {len(new_papers)} 篇新论文")

        # 3. 获取新论文的各项指标
        logger.info("步骤3: 获取新论文的各项指标")
        for i, paper in enumerate(new_papers):
            logger.info(f"[{i+1}/{len(new_papers)}] 处理: {paper.arxiv_id}")
            self._enrich_paper(paper)

        # 4. 保存到数据库
        logger.info("步骤4: 保存到数据库")
        for paper in new_papers:
            paper.is_new = True

        success = paper_repo.insert_papers(new_papers)

        if success:
            logger.info(f"[FetchService] 完成! 成功入库 {len(new_papers)} 篇新论文")
        else:
            logger.error("[FetchService] 保存失败")

    def _enrich_paper(self, paper: Paper):
        """获取论文的各项指标（根据配置开关决定是否抓取）"""

        # ArXiv 详细信息
        if settings.SCRAPER_ARXIV_ENABLED:
            arxiv_data = self.arxiv_scraper.fetch(paper.arxiv_id)
            if arxiv_data:
                paper.title = arxiv_data.get('title') or paper.title
                paper.authors = arxiv_data.get('authors') or paper.authors
                if arxiv_data.get('pub_date'):
                    from datetime import date
                    try:
                        paper.pub_date = date.fromisoformat(arxiv_data['pub_date'])
                    except (ValueError, TypeError):
                        pass

        # Mendeley 阅读数
        if settings.SCRAPER_MENDELEY_ENABLED:
            mendeley_data = self.mendeley_scraper.fetch(paper.arxiv_id)
            if mendeley_data:
                paper.reader_count = mendeley_data.get('reader_count', 0) or 0
                paper.journal = mendeley_data.get('journal')

        # Altmetric 社交指标（x_num 统一由此接口提供）
        if settings.SCRAPER_ALTMETRIC_ENABLED:
            altmetric_data = self.altmetric_scraper.fetch(paper.arxiv_id)
            if altmetric_data:
                paper.x_num = altmetric_data.get('x_num', 0) or 0
                paper.cited_by_msm_count = altmetric_data.get('cited_by_msm_count', 0) or 0
                paper.altmetric_score = altmetric_data.get('altmetric_score', 0.0) or 0.0

        # GitHub 信息
        if settings.SCRAPER_GITHUB_ENABLED and paper.github_url:
            github_data = self.github_scraper.fetch(paper.github_url)
            if github_data:
                paper.star_num = github_data.get('star_num', 0) or 0
                paper.fork_num = github_data.get('fork_num', 0) or 0
                paper.watch_num = github_data.get('watch_num', 0) or 0

        # Semantic Scholar 引用数
        if settings.SCRAPER_SEMANTIC_SCHOLAR_ENABLED:
            citation_data = self.semantic_scholar_scraper.fetch(paper.arxiv_id)
            if citation_data:
                paper.citation_count = citation_data.get('citation_count', 0) or 0
                paper.reference_count = citation_data.get('reference_count', 0) or 0


# 全局服务实例
fetch_service = FetchService()
