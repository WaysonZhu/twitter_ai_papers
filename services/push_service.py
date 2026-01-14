"""
GitHub 推送服务
功能3：计算 TopK 论文并推送到 GitHub
"""
import base64
import logging
from datetime import datetime
from typing import List
from collections import defaultdict

import requests

from config.settings import settings
from database.repository import paper_repo
from algorithms.ranking import ranking_algorithm
from models.paper import Paper

logger = logging.getLogger(__name__)


class PushService:
    """GitHub 推送服务"""

    def __init__(self):
        self.github_api_url = "https://api.github.com/repos"

    def run(self):
        """执行 GitHub 推送"""
        logger.info("=" * 60)
        logger.info(f"[PushService] 开始 GitHub 推送 - {datetime.now()}")
        logger.info("=" * 60)

        # 0. 检查当天是否已经推送过
        today_pushed = paper_repo.get_today_pushed_count()
        if today_pushed >= settings.TOPK_COUNT:
            logger.info(f"今天已推送 {today_pushed} 篇论文，跳过本次推送")
            # 即使跳过新论文推送，也更新历史页面
            self._update_history_page()
            return

        # 1. 获取未推送过的论文
        logger.info("步骤1: 获取未推送过的论文")
        papers = paper_repo.get_unpushed_papers()

        if not papers:
            logger.info("没有新论文需要推送")
            # 即使没有新论文，也可以更新历史页面
            self._update_history_page()
            return

        logger.info(f"共 {len(papers)} 篇论文待评分")

        # 2. 使用评分算法计算排名
        logger.info("步骤2: 计算评分排名")
        top_papers = ranking_algorithm.rank(papers, top_k=settings.TOPK_COUNT)

        if not top_papers:
            logger.info("没有符合条件的论文")
            return

        logger.info(f"TopK 论文:")
        for i, p in enumerate(top_papers):
            logger.info(f"  {i+1}. {p.arxiv_id} (score={p.score:.2f})")

        # 3. 获取历史论文（用于生成首页）
        logger.info("步骤3: 获取历史论文")
        history_papers = paper_repo.get_papers_for_history(days=settings.HISTORY_DAYS)

        # 合并当天 TopK 和历史论文
        index_papers = top_papers + history_papers

        # 4. 生成 README 内容
        logger.info("步骤4: 生成 README 内容")
        readme_content = self._generate_readme(index_papers)

        if not readme_content:
            logger.error("README 内容生成失败")
            return

        # 5. 推送到 GitHub
        logger.info("步骤5: 推送到 GitHub")
        success = self._push_to_github(readme_content, is_history=False)

        if success:
            # 6. 记录到历史表
            logger.info("步骤6: 记录推送历史")
            paper_repo.save_to_history(top_papers)

            # 7. 更新历史页面
            self._update_history_page()

            logger.info(f"[PushService] 完成! 成功推送 {len(top_papers)} 篇论文")
        else:
            logger.error("[PushService] 推送失败")

    def _update_history_page(self):
        """更新历史页面"""
        logger.info("更新历史页面...")
        all_history = paper_repo.get_papers_for_history(days=5000)  # 获取所有历史

        if not all_history:
            return

        history_content = self._generate_readme(all_history, is_history=True)
        if history_content:
            self._push_to_github(history_content, is_history=True)

    def _generate_readme(self, papers: List[Paper], is_history: bool = False) -> str:
        """生成 README 内容"""
        if not papers:
            return ""

        # 按日期分组
        papers_by_date = defaultdict(list)
        today_str = datetime.now().strftime('%Y-%m-%d')
        for paper in papers:
            if is_history:
                # 历史页面：按推送日期（create_time）分组
                date_str = today_str
                if paper.create_time:
                    date_str = paper.create_time.strftime('%Y-%m-%d')
            else:
                # 首页：今天推送的论文统一显示今天日期
                date_str = today_str
            papers_by_date[date_str].append(paper)

        # 生成头部
        img_path = "../figures/hr.gif" if is_history else "./figures/hr.gif"
        content = f"""<div align="center">

<img width="200%" src="{img_path}" />

# AI Spotlight: Trending Research Papers
Welcome to AI Spotlight — a curated list of the latest and trending AI research papers.

</div>

"""

        # 按日期倒序生成内容
        sorted_dates = sorted(papers_by_date.keys(), reverse=True)

        for date in sorted_dates:
            content += f"\n### {date}\n\n"

            for paper in papers_by_date[date]:
                # 论文标题
                title_line = f"**[{paper.title}]({paper.url})**"
                if paper.is_new:
                    title_line += " NEW"
                content += title_line + "\n\n"

                # arxiv 发布日期
                if paper.pub_date:
                    pub_date_str = paper.pub_date.strftime('%Y-%m-%d') if hasattr(paper.pub_date, 'strftime') else str(paper.pub_date)
                    content += f"*Published: {pub_date_str}*\n\n"

                # 作者
                authors = paper.authors if paper.authors else "Unknown"
                authors_list = [a.strip() for a in authors.split(',')]
                if len(authors_list) > 25:
                    authors_list = authors_list[:25] + ["etc."]
                content += f"*{', '.join(authors_list)}*\n\n"

                # 徽章
                badges = []
                if paper.citation_count > 0:
                    badges.append(f"![](https://img.shields.io/badge/Citations-{paper.citation_count}-9cf)")
                if paper.x_num > 0:
                    badges.append(f"![](https://img.shields.io/badge/Twitter%20Mentions-{paper.x_num}-1DA1F2)")
                if paper.github_url and paper.star_num > 0:
                    badges.append(f"[![](https://img.shields.io/badge/GitHub%20Stars-{paper.star_num:,}-blue)]({paper.github_url})")
                if paper.reader_count > 0:
                    badges.append(f"![](https://img.shields.io/badge/Mendeley%20Readers-{paper.reader_count}-red)")
                if paper.cited_by_msm_count > 0:
                    badges.append(f"![](https://img.shields.io/badge/Mainstream%20Media%20Mentions-{paper.cited_by_msm_count}-green)")

                if badges:
                    content += " ".join(badges) + "\n\n"

                content += "---\n\n"

        # 底部链接
        if is_history:
            content += "\n[Back to latest news](https://github.com/{}/{})\n".format(
                settings.GITHUB_OWNER, settings.GITHUB_REPO
            )
        else:
            content += "\n[Complete history news](./history/README.md)\n"

        return content

    def _push_to_github(self, content: str, is_history: bool = False) -> bool:
        """推送内容到 GitHub"""
        if not content or not content.strip():
            logger.error("README 内容为空")
            return False

        if not settings.GITHUB_TOKEN:
            logger.error("未配置 GITHUB_TOKEN")
            return False

        # 构建 API URL
        if is_history:
            url = f"{self.github_api_url}/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/contents/history/README.md"
        else:
            url = f"{self.github_api_url}/{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}/contents/README.md"

        headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            # 检查文件是否存在
            response = requests.get(url, headers=headers)
            sha = None
            if response.status_code == 200:
                sha = response.json().get("sha")

            # 准备上传数据
            content_base64 = base64.b64encode(content.encode('utf-8')).decode()
            data = {
                "message": "Hot AI Papers Update",
                "content": content_base64,
                "branch": settings.GITHUB_BRANCH,
            }
            if sha:
                data["sha"] = sha

            # 上传文件
            response = requests.put(url, json=data, headers=headers)

            if response.status_code in [200, 201]:
                logger.info(f"GitHub 推送成功: {'history/' if is_history else ''}README.md")
                return True
            else:
                logger.error(f"GitHub 推送失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"GitHub 推送异常: {e}")
            return False


# 全局服务实例
push_service = PushService()
