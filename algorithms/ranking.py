"""
论文评分排名算法
用于计算论文的综合得分并排序
"""
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any

from models.paper import Paper

logger = logging.getLogger(__name__)


class RankingAlgorithm:
    """论文评分排名算法"""

    # 评分阈值（低于此值的论文会被过滤）
    MIN_STAR_NUM = 50
    MIN_X_NUM = 20
    MIN_CITED_BY_MSM = 1
    MIN_CITATION_COUNT = 5
    MIN_READER_COUNT = 10

    # 论文时间限制（月数）
    MAX_PAPER_AGE_MONTHS = 6

    def _is_within_time_limit(self, arxiv_id: str) -> bool:
        """
        检查论文是否在时间限制内（半年内）
        arxiv_id 格式: YYMM.NNNNN (如 2309.06180 表示 2023年9月)
        """
        try:
            yymm = arxiv_id.split('.')[0]
            if len(yymm) != 4:
                return False

            year = 2000 + int(yymm[:2])
            month = int(yymm[2:])

            paper_date = datetime(year, month, 1)
            now = datetime.now()

            # 计算月份差
            months_diff = (now.year - paper_date.year) * 12 + (now.month - paper_date.month)

            return months_diff <= self.MAX_PAPER_AGE_MONTHS
        except (ValueError, IndexError):
            logger.warning(f"无法解析 arxiv_id 日期: {arxiv_id}")
            return False

    def calculate_score(self, paper: Paper) -> Tuple[float, Dict[str, Any]]:
        """
        计算论文评分

        Args:
            paper: 论文对象

        Returns:
            (score, reasons) - 分数和评分原因
        """
        score = 0.0
        reasons = {}

        # 过滤低质量论文
        if (paper.star_num < self.MIN_STAR_NUM and
            paper.x_num < self.MIN_X_NUM and
            paper.cited_by_msm_count < self.MIN_CITED_BY_MSM and
            paper.citation_count < self.MIN_CITATION_COUNT and
            paper.reader_count < self.MIN_READER_COUNT):
            reasons['reason'] = '所有指标都过低'
            return 0, reasons

        # GitHub 维度 (最高 70 分)
        if paper.github_url:
            score += 20  # 有仓库 +20
            reasons['github_url'] = paper.github_url
            star_score = min(paper.star_num / 10, 50)  # Star/10, 上限50
            score += star_score
            reasons['star_num'] = paper.star_num

        # Citation 维度 (最高 50 分)
        if paper.citation_count > 0:
            citation_score = min(paper.citation_count / 20, 50)  # 引用数/20, 上限50
            score += citation_score
            reasons['citation_count'] = paper.citation_count

        # Mendeley 阅读数 (最高 20 分)
        if paper.reader_count > 0:
            read_score = min(paper.reader_count / 50, 20)  # 阅读数/50, 上限20
            score += read_score
            reasons['n_read'] = paper.reader_count

        # Twitter/X 提及 (最高 30 分)
        if paper.x_num > 100:
            score += 30  # >100次 +30
            reasons['x_num'] = paper.x_num
        elif paper.x_num > 20:
            score += 10  # >20次 +10
            reasons['x_num'] = paper.x_num

        # 权威媒体报道 (最高 30 分)
        if paper.cited_by_msm_count > 0:
            score += 30  # 有权威媒体报道 +30
            reasons['cited_by_msm_count'] = paper.cited_by_msm_count

        return score, reasons

    def rank(self, papers: List[Paper], top_k: int = None) -> List[Paper]:
        """
        对论文进行评分并排序

        Args:
            papers: 论文列表
            top_k: 返回前 K 篇，None 返回全部

        Returns:
            排序后的论文列表（包含 score 和 score_reasons）
        """
        scored_papers = []
        filtered_by_time = 0

        for paper in papers:
            # 过滤超过半年的论文
            if not self._is_within_time_limit(paper.arxiv_id):
                filtered_by_time += 1
                continue

            score, reasons = self.calculate_score(paper)
            if score > 0:
                paper.score = score
                paper.score_reasons = reasons
                scored_papers.append(paper)

        if filtered_by_time > 0:
            logger.info(f"过滤掉 {filtered_by_time} 篇超过 {self.MAX_PAPER_AGE_MONTHS} 个月的论文")

        # 按分数降序排序
        scored_papers.sort(key=lambda p: p.score, reverse=True)

        logger.info(f"评分完成: {len(scored_papers)}/{len(papers)} 篇论文通过筛选")

        if top_k:
            return scored_papers[:top_k]
        return scored_papers


# 全局算法实例
ranking_algorithm = RankingAlgorithm()
