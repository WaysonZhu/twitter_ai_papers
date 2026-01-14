"""
统一配置管理模块
从环境变量加载配置，提供类型安全的访问
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件（override=True 确保 .env 优先于系统环境变量）
load_dotenv(override=True)


def _get_bool(key: str, default: bool = False) -> bool:
    """从环境变量获取布尔值"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


@dataclass
class Settings:
    """应用配置类"""

    # ==========================================================================
    # 指标抓取开关
    # ==========================================================================
    SCRAPER_ARXIV_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_ARXIV_ENABLED', True))
    SCRAPER_MENDELEY_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_MENDELEY_ENABLED', True))
    SCRAPER_ALTMETRIC_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_ALTMETRIC_ENABLED', False))
    SCRAPER_GITHUB_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_GITHUB_ENABLED', True))
    SCRAPER_SEMANTIC_SCHOLAR_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_SEMANTIC_SCHOLAR_ENABLED', True))

    # ==========================================================================
    # X Trending 数据源配置
    # ==========================================================================
    SCRAPER_X_TRENDING_ENABLED: bool = field(default_factory=lambda: _get_bool('SCRAPER_X_TRENDING_ENABLED', False))
    XAI_API_KEY: str = field(default_factory=lambda: os.getenv('XAI_API_KEY', ''))
    X_TRENDING_MONTHS: int = field(default_factory=lambda: int(os.getenv('X_TRENDING_MONTHS', '3')))
    X_TRENDING_MAX_PAPERS: int = field(default_factory=lambda: int(os.getenv('X_TRENDING_MAX_PAPERS', '20')))

    # ==========================================================================
    # 数据库配置
    # ==========================================================================
    DB_HOST: str = field(default_factory=lambda: os.getenv('DB_HOST', 'localhost'))
    DB_PORT: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '3306')))
    DB_USER: str = field(default_factory=lambda: os.getenv('DB_USER', 'root'))
    DB_PASSWORD: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    DB_DATABASE: str = field(default_factory=lambda: os.getenv('DB_DATABASE', 'ai_papers'))
    DB_CHARSET: str = field(default_factory=lambda: os.getenv('DB_CHARSET', 'utf8mb4'))

    # ==========================================================================
    # GitHub 配置
    # ==========================================================================
    GITHUB_TOKEN: str = field(default_factory=lambda: os.getenv('GITHUB_TOKEN', ''))
    GITHUB_OWNER: str = field(default_factory=lambda: os.getenv('GITHUB_OWNER', ''))
    GITHUB_REPO: str = field(default_factory=lambda: os.getenv('GITHUB_REPO', ''))
    GITHUB_BRANCH: str = field(default_factory=lambda: os.getenv('GITHUB_BRANCH', 'main'))

    # ==========================================================================
    # Mendeley API 配置
    # ==========================================================================
    MENDELEY_CLIENT_ID: str = field(default_factory=lambda: os.getenv('MENDELEY_CLIENT_ID', ''))
    MENDELEY_CLIENT_SECRET: str = field(default_factory=lambda: os.getenv('MENDELEY_CLIENT_SECRET', ''))

    # ==========================================================================
    # Semantic Scholar API 配置
    # ==========================================================================
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    )

    # ==========================================================================
    # 定时任务配置
    # ==========================================================================
    FETCH_ENABLED: bool = field(default_factory=lambda: _get_bool('FETCH_ENABLED', True))
    FETCH_CRON: str = field(default_factory=lambda: os.getenv('FETCH_CRON', '0 8 * * *'))

    UPDATE_ENABLED: bool = field(default_factory=lambda: _get_bool('UPDATE_ENABLED', True))
    UPDATE_CRON: str = field(default_factory=lambda: os.getenv('UPDATE_CRON', '0 */6 * * *'))
    UPDATE_BATCH_SIZE: int = field(default_factory=lambda: int(os.getenv('UPDATE_BATCH_SIZE', '100')))

    PUSH_ENABLED: bool = field(default_factory=lambda: _get_bool('PUSH_ENABLED', True))
    PUSH_CRON: str = field(default_factory=lambda: os.getenv('PUSH_CRON', '0 9 * * *'))

    # ==========================================================================
    # 推送算法配置
    # ==========================================================================
    TOPK_COUNT: int = field(default_factory=lambda: int(os.getenv('TOPK_COUNT', '5')))
    HISTORY_DAYS: int = field(default_factory=lambda: int(os.getenv('HISTORY_DAYS', '5')))

    # ==========================================================================
    # 代理配置
    # ==========================================================================
    HTTP_PROXY: Optional[str] = field(default_factory=lambda: os.getenv('HTTP_PROXY'))
    HTTPS_PROXY: Optional[str] = field(default_factory=lambda: os.getenv('HTTPS_PROXY'))
    NO_PROXY: Optional[str] = field(default_factory=lambda: os.getenv('NO_PROXY'))

    # ==========================================================================
    # 日志配置
    # ==========================================================================
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    LOG_DIR: str = field(default_factory=lambda: os.getenv('LOG_DIR', './logs'))

    # ==========================================================================
    # HTTP 客户端配置
    # ==========================================================================
    HTTP_TIMEOUT: int = field(default_factory=lambda: int(os.getenv('HTTP_TIMEOUT', '30')))
    HTTP_RETRIES: int = field(default_factory=lambda: int(os.getenv('HTTP_RETRIES', '3')))

    def get_db_config(self) -> dict:
        """获取数据库连接配置字典"""
        return {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'database': self.DB_DATABASE,
            'charset': self.DB_CHARSET,
        }

    def get_proxy_config(self) -> Optional[dict]:
        """
        获取代理配置

        返回格式：
        - requests 库使用: {'http': '...', 'https': '...'}
        - httpx 库使用: {'http://': '...', 'https://': '...'}

        注意：NO_PROXY 通过环境变量自动生效（python-dotenv 已加载到 os.environ）
        requests 和 httpx 都会自动检查 NO_PROXY 环境变量
        """
        if self.HTTP_PROXY or self.HTTPS_PROXY:
            return {
                # requests 格式
                'http': self.HTTP_PROXY,
                'https': self.HTTPS_PROXY,
                # httpx 格式
                'http://': self.HTTP_PROXY,
                'https://': self.HTTPS_PROXY,
            }
        return None


# 全局单例
settings = Settings()
