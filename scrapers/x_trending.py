"""
X Trending 论文抓取器
通过 xAI Grok API 搜索 X 上热门的 AI arxiv 论文
"""
import os
import re
import logging
from datetime import datetime
from typing import List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field

from scrapers.base import BaseScraper
from models.paper import Paper
from config.settings import settings

logger = logging.getLogger(__name__)


# Pydantic 模型用于结构化输出
class ArxivPaperResponse(BaseModel):
    title: str = Field(description="论文标题")
    arxiv_url: str = Field(description="arxiv 论文链接")
    github_url: str = Field(default="", description="GitHub 仓库链接，如果帖子中没有提供则为空字符串")
    authors: str = Field(description="论文作者")
    summary: str = Field(description="论文简介或帖子中的描述")
    tweet_username: str = Field(description="发帖用户名")
    tweet_content: str = Field(description="原帖内容摘要")
    likes: int = Field(description="帖子点赞数")
    reposts: int = Field(description="转帖数")
    timestamp: str = Field(description="发帖时间")


class HotArxivPapersResponse(BaseModel):
    papers: List[ArxivPaperResponse] = Field(description="热门 arxiv 论文列表")
    search_date: str = Field(description="搜索日期")
    total_found: int = Field(description="找到的论文数量")


class XTrendingScraper(BaseScraper):
    """X Trending 论文抓取器"""

    def __init__(self):
        super().__init__()
        self.api_key = settings.XAI_API_KEY
        self.months = settings.X_TRENDING_MONTHS
        self.max_papers = settings.X_TRENDING_MAX_PAPERS

    def fetch(self, identifier: str = None) -> List[Paper]:
        """
        搜索 X 上热门 AI arxiv 论文

        Returns:
            过滤验证后的论文列表
        """
        if not self.api_key:
            logger.warning("[X_TRENDING] XAI_API_KEY 未配置，跳过 X Trending 抓取")
            return []

        try:
            # 延迟导入，避免未安装时报错
            from xai_sdk import Client
            from xai_sdk.chat import user
            from xai_sdk.tools import x_search
        except ImportError:
            logger.error("[X_TRENDING] xai_sdk 未安装，请运行: pip install xai-sdk")
            return []

        logger.info(f"[X_TRENDING] 开始搜索 X 上热门 AI arxiv 论文")

        # 设置 API Key
        os.environ["XAI_API_KEY"] = self.api_key

        # 计算有效的 arxiv ID 前缀
        valid_prefixes = self._get_valid_arxiv_prefixes()
        logger.info(f"[X_TRENDING] 有效 arxiv ID 前缀（{self.months}个月内）: {valid_prefixes}")

        try:
            # 初始化客户端
            client = Client()

            chat = client.chat.create(
                model="grok-4-1-fast-non-reasoning",
                tools=[x_search()],
                max_turns=10,
                response_format=HotArxivPapersResponse
            )

            # 构建搜索 prompt
            search_query = f"""
搜索 X 上讨论最热门的 AI/机器学习相关 arxiv 论文。

要求：
1. 必须包含真实的 arxiv.org 链接（格式如 https://arxiv.org/abs/YYMM.XXXXX）
2. 必须包含 GitHub 仓库链接（格式如 https://github.com/xxx/xxx），优先返回有代码开源的论文
3. 论文必须是最近 {self.months} 个月内发布的，即 arxiv ID 必须以这些前缀开头: {', '.join(valid_prefixes)}
4. 按热度（点赞+转发数）排序
5. 只返回同时有 arxiv 链接和 GitHub 仓库的帖子
6. 关注 AI、machine learning、deep learning、LLM、NLP、computer vision、reasoning、agents 等领域
7. 返回前 50 条最热门的，确保能筛选出 {self.max_papers} 篇有效论文

请搜索包含 "arxiv.org" 和 "github.com" 的热门帖子，筛选出 AI 相关的论文讨论。
"""

            chat.append(user(search_query))

            # 获取响应
            logger.info("[X_TRENDING] 正在调用 Grok API...")
            response, structured_data = chat.parse(HotArxivPapersResponse)

            logger.info(f"[X_TRENDING] API 返回 {len(structured_data.papers)} 篇论文")

            # 过滤和验证
            papers = self._filter_and_validate(structured_data.papers, valid_prefixes)

            logger.info(f"[X_TRENDING] 过滤验证后剩余 {len(papers)} 篇论文")
            return papers

        except Exception as e:
            logger.error(f"[X_TRENDING] 抓取失败: {e}")
            return []

    def _get_valid_arxiv_prefixes(self) -> List[str]:
        """计算有效的 arxiv ID 前缀（最近 N 个月）"""
        now = datetime.now()
        valid_prefixes = []

        for i in range(self.months + 1):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            prefix = f"{year % 100:02d}{month:02d}"
            valid_prefixes.append(prefix)

        return sorted(set(valid_prefixes))

    def _extract_arxiv_id(self, url: str) -> str:
        """从 URL 中提取 arxiv ID"""
        match = re.search(r'(\d{4}\.\d{4,5})', url)
        return match.group(1) if match else ""

    def _is_valid_arxiv_id(self, arxiv_id: str, valid_prefixes: List[str]) -> bool:
        """检查 arxiv ID 是否在有效时间范围内"""
        if not arxiv_id:
            return False
        prefix = arxiv_id[:4]
        return prefix in valid_prefixes

    def _check_arxiv_url(self, arxiv_id: str) -> tuple:
        """检查 arxiv 链接是否能成功访问（HTTP 200）"""
        url = f"https://arxiv.org/abs/{arxiv_id}"
        try:
            import requests
            response = requests.head(url, timeout=10, allow_redirects=True)
            is_valid = response.status_code == 200
            return arxiv_id, is_valid
        except Exception as e:
            logger.debug(f"[X_TRENDING] 验证失败 {arxiv_id}: {e}")
            return arxiv_id, False

    def _extract_github_url(self, url: str) -> str:
        """提取并规范化 GitHub 仓库 URL"""
        if not url:
            return ""
        # 匹配 github.com/owner/repo 格式
        match = re.search(r'https?://github\.com/([^/\s]+/[^/\s]+)', url)
        if match:
            return f"https://github.com/{match.group(1).rstrip('/')}"
        return ""

    def _filter_and_validate(
        self,
        api_papers: List[ArxivPaperResponse],
        valid_prefixes: List[str]
    ) -> List[Paper]:
        """
        四层过滤：
        1. arxiv ID 时间范围过滤
        2. GitHub URL 验证
        3. 去重
        4. HTTP 200 验证
        """
        seen_arxiv_ids: Set[str] = set()
        candidate_papers = []

        # 第一层 + 第二层 + 第三层：时间范围过滤 + GitHub URL 验证 + 去重
        for p in api_papers:
            arxiv_id = self._extract_arxiv_id(p.arxiv_url)
            github_url = self._extract_github_url(p.github_url)

            if not arxiv_id:
                logger.debug(f"[X_TRENDING] 跳过（无效 arxiv 链接）: {p.arxiv_url}")
                continue
            if not github_url:
                logger.debug(f"[X_TRENDING] 跳过（无 GitHub 仓库）: {arxiv_id}")
                continue
            if arxiv_id in seen_arxiv_ids:
                logger.debug(f"[X_TRENDING] 跳过（重复）: {arxiv_id}")
                continue
            if not self._is_valid_arxiv_id(arxiv_id, valid_prefixes):
                logger.debug(f"[X_TRENDING] 跳过（超过{self.months}个月）: {arxiv_id}")
                continue

            seen_arxiv_ids.add(arxiv_id)
            candidate_papers.append((arxiv_id, github_url, p))

        logger.info(f"[X_TRENDING] 时间+GitHub+去重过滤后: {len(candidate_papers)} 篇")

        # 第四层：HTTP 200 验证（并发）
        logger.info("[X_TRENDING] 验证 arxiv 链接可访问性...")
        valid_arxiv_ids: Set[str] = set()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self._check_arxiv_url, arxiv_id): arxiv_id
                for arxiv_id, _, _ in candidate_papers
            }
            for future in as_completed(futures):
                arxiv_id, is_valid = future.result()
                if is_valid:
                    logger.debug(f"[X_TRENDING] ✓ {arxiv_id} 可访问")
                    valid_arxiv_ids.add(arxiv_id)
                else:
                    logger.debug(f"[X_TRENDING] ✗ {arxiv_id} 无法访问")

        # 转换为 Paper 对象
        papers = []
        for arxiv_id, github_url, p in candidate_papers:
            if arxiv_id not in valid_arxiv_ids:
                continue

            paper = Paper(
                arxiv_id=arxiv_id,
                title=p.title,
                authors=p.authors,
                abstract=p.summary,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                github_url=github_url,  # 添加 GitHub 仓库地址
                x_num=0,  # x_num 统一由 Altmetric API 填充
                from_source="X_TRENDING",
            )
            paper._x_heat = p.likes + p.reposts  # 临时热度用于排序
            papers.append(paper)

        # 按 X 热度排序，取前 max_papers 篇
        papers.sort(key=lambda x: getattr(x, '_x_heat', 0), reverse=True)
        papers = papers[:self.max_papers]

        return papers
