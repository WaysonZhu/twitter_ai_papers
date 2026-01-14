"""
GitHub 仓库信息抓取器
从 GitHub API 获取仓库的 star、fork、watch 数据
"""
import re
import logging
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper
from config.settings import settings

logger = logging.getLogger(__name__)


class GitHubScraper(BaseScraper):
    """GitHub 仓库信息抓取器"""

    API_BASE_URL = "https://api.github.com/repos"

    def fetch(self, github_url: str) -> Optional[Dict[str, Any]]:
        """
        获取 GitHub 仓库信息

        Args:
            github_url: GitHub 仓库 URL，如 https://github.com/owner/repo

        Returns:
            包含 star_num, fork_num, watch_num 的字典
        """
        if not github_url:
            return {'github_url': None, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}

        logger.info(f"[GitHub] 获取: {github_url}")

        # 从 URL 提取 owner/repo
        match = re.match(r"https://github\.com/([^/]+/[^/]+)", github_url)
        if not match:
            self._log_error("GitHub", github_url, "无效的 GitHub URL")
            return {'github_url': github_url, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}

        repo_path = match.group(1)
        # 移除可能的 .git 后缀或其他路径
        repo_path = repo_path.split('/tree/')[0].split('/blob/')[0]
        if repo_path.endswith('.git'):
            repo_path = repo_path[:-4]

        api_url = f"{self.API_BASE_URL}/{repo_path}"

        # 构建请求头
        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            # 新版 GitHub PAT (github_pat_*) 使用 Bearer，旧版 (ghp_*) 使用 token
            if settings.GITHUB_TOKEN.startswith("github_pat_"):
                headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
            else:
                headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        try:
            response = self.httpx_client.get(api_url, headers=headers)

            # 如果 Token 认证失败 (401)，尝试无 Token 请求
            if response and response.status_code == 401:
                logger.warning("[GitHub] Token 认证失败，尝试无 Token 请求")
                headers_no_auth = {"Accept": "application/vnd.github.v3+json"}
                response = self.httpx_client.get(api_url, headers=headers_no_auth)

            if not response:
                self._log_error("GitHub", github_url, "请求失败")
                return {'github_url': github_url, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}

            if response.status_code == 404:
                self._log_not_found("GitHub", github_url)
                return {'github_url': github_url, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}

            if response.status_code != 200:
                self._log_error("GitHub", github_url, f"状态码: {response.status_code}")
                return {'github_url': github_url, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}

            data = response.json()

            result = {
                'github_url': github_url,
                'star_num': data.get('stargazers_count', 0) or 0,
                'fork_num': data.get('forks_count', 0) or 0,
                'watch_num': data.get('subscribers_count', 0) or 0,
            }

            self._log_success("GitHub", github_url)
            return result

        except Exception as e:
            self._log_error("GitHub", github_url, str(e))
            return {'github_url': github_url, 'star_num': 0, 'fork_num': 0, 'watch_num': 0}
