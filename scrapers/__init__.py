"""
数据抓取器模块
"""
from scrapers.base import BaseScraper
from scrapers.hf_trending import HFTrendingScraper
from scrapers.x_trending import XTrendingScraper
from scrapers.arxiv import ArxivScraper
from scrapers.mendeley import MendeleyScraper
from scrapers.altmetric import AltmetricScraper
from scrapers.github_scraper import GitHubScraper
from scrapers.semantic_scholar import SemanticScholarScraper

__all__ = [
    'BaseScraper',
    'HFTrendingScraper',
    'XTrendingScraper',
    'ArxivScraper',
    'MendeleyScraper',
    'AltmetricScraper',
    'GitHubScraper',
    'SemanticScholarScraper',
]
