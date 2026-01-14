"""
更新指标服务
功能2：定期更新已有论文的所有指标
"""
import logging
from datetime import datetime

from config.settings import settings
from scrapers.mendeley import MendeleyScraper
from scrapers.altmetric import AltmetricScraper
from scrapers.github_scraper import GitHubScraper
from scrapers.semantic_scholar import SemanticScholarScraper
from database.repository import paper_repo
from models.paper import Paper

logger = logging.getLogger(__name__)


class UpdateService:
    """更新指标服务"""

    def __init__(self):
        self.mendeley_scraper = MendeleyScraper()
        self.altmetric_scraper = AltmetricScraper()
        self.github_scraper = GitHubScraper()
        self.semantic_scholar_scraper = SemanticScholarScraper()

    def run(self):
        """执行指标更新（滚动更新）"""
        logger.info("=" * 60)
        logger.info(f"[UpdateService] 开始滚动更新指标 - {datetime.now()}")
        logger.info("=" * 60)

        # 1. 获取最久未更新的论文（滚动更新）
        batch_size = settings.UPDATE_BATCH_SIZE
        total_count = paper_repo.get_total_paper_count()

        logger.info(f"步骤1: 获取最久未更新的 {batch_size} 篇论文")
        papers = paper_repo.get_papers_for_update(limit=batch_size)

        if not papers:
            logger.info("没有论文需要更新")
            return

        logger.info(f"本次更新 {len(papers)} 篇论文（数据库共 {total_count} 篇）")

        # 2. 更新每篇论文的指标
        logger.info("步骤2: 更新各项指标")
        success_count = 0
        fail_count = 0

        for i, paper in enumerate(papers):
            logger.info(f"[{i+1}/{len(papers)}] 更新: {paper.arxiv_id}")

            try:
                self._update_metrics(paper)
                if paper_repo.update_paper_metrics(paper):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"更新失败 {paper.arxiv_id}: {e}")
                fail_count += 1

        logger.info(f"[UpdateService] 完成! 成功: {success_count}, 失败: {fail_count}")

    def _update_metrics(self, paper: Paper):
        """更新论文的各项指标（根据配置开关决定是否抓取）"""

        # Mendeley 阅读数
        if settings.SCRAPER_MENDELEY_ENABLED:
            mendeley_data = self.mendeley_scraper.fetch(paper.arxiv_id)
            if mendeley_data:
                paper.reader_count = mendeley_data.get('reader_count', 0) or paper.reader_count
                paper.journal = mendeley_data.get('journal') or paper.journal

        # Altmetric 社交指标
        if settings.SCRAPER_ALTMETRIC_ENABLED:
            altmetric_data = self.altmetric_scraper.fetch(paper.arxiv_id)
            if altmetric_data:
                paper.x_num = altmetric_data.get('x_num', 0) or paper.x_num
                paper.cited_by_msm_count = altmetric_data.get('cited_by_msm_count', 0) or paper.cited_by_msm_count

        # GitHub 信息
        if settings.SCRAPER_GITHUB_ENABLED and paper.github_url:
            github_data = self.github_scraper.fetch(paper.github_url)
            if github_data:
                paper.star_num = github_data.get('star_num', 0) or paper.star_num
                paper.fork_num = github_data.get('fork_num', 0) or paper.fork_num
                paper.watch_num = github_data.get('watch_num', 0) or paper.watch_num

        # Semantic Scholar 引用数
        if settings.SCRAPER_SEMANTIC_SCHOLAR_ENABLED:
            citation_data = self.semantic_scholar_scraper.fetch(paper.arxiv_id)
            if citation_data:
                paper.citation_count = citation_data.get('citationCount', 0) or paper.citation_count


# 全局服务实例
update_service = UpdateService()
