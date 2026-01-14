"""
论文数据模型
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any


@dataclass
class Paper:
    """论文数据类"""

    # 基本信息
    arxiv_id: str
    title: str = ""
    authors: str = ""
    abstract: str = ""
    pub_date: Optional[date] = None
    url: str = ""
    pdf_url: str = ""

    # GitHub 信息
    github_url: Optional[str] = None
    star_num: int = 0
    fork_num: int = 0
    watch_num: int = 0

    # Mendeley 指标
    reader_count: int = 0  # n_read
    journal: Optional[str] = None

    # Altmetric 指标
    x_num: int = 0  # Twitter/X 提及数
    cited_by_msm_count: int = 0  # 主流媒体引用数
    altmetric_score: float = 0.0

    # Semantic Scholar 指标
    citation_count: int = 0
    reference_count: int = 0

    # 元数据
    from_source: str = "HF_TRENDING"
    display_order: Optional[int] = None
    is_new: bool = False
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    # 评分相关（用于 GitHub 推送）
    score: float = 0.0
    score_reasons: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'arxiv_id': self.arxiv_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'pub_date': self.pub_date.isoformat() if self.pub_date else None,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'github_url': self.github_url,
            'star_num': self.star_num,
            'fork_num': self.fork_num,
            'watch_num': self.watch_num,
            'reader_count': self.reader_count,
            'journal': self.journal,
            'x_num': self.x_num,
            'cited_by_msm_count': self.cited_by_msm_count,
            'altmetric_score': self.altmetric_score,
            'citation_count': self.citation_count,
            'reference_count': self.reference_count,
            'from_source': self.from_source,
            'display_order': self.display_order,
            'is_new': self.is_new,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Paper':
        """从字典创建实例"""
        pub_date = data.get('pub_date')
        if pub_date and isinstance(pub_date, str):
            pub_date = date.fromisoformat(pub_date)

        return cls(
            arxiv_id=data.get('arxiv_id', ''),
            title=data.get('title', ''),
            authors=data.get('authors', ''),
            abstract=data.get('abstract', ''),
            pub_date=pub_date,
            url=data.get('url', ''),
            pdf_url=data.get('pdf_url', ''),
            github_url=data.get('github_url'),
            star_num=data.get('star_num', 0) or 0,
            fork_num=data.get('fork_num', 0) or 0,
            watch_num=data.get('watch_num', 0) or 0,
            reader_count=data.get('reader_count', 0) or data.get('n_read', 0) or 0,
            journal=data.get('journal'),
            x_num=data.get('x_num', 0) or 0,
            cited_by_msm_count=data.get('cited_by_msm_count', 0) or 0,
            altmetric_score=data.get('altmetric_score', 0.0) or 0.0,
            citation_count=data.get('citation_count', 0) or 0,
            reference_count=data.get('reference_count', 0) or 0,
            from_source=data.get('from_source', 'HF_TRENDING'),
            display_order=data.get('display_order'),
            is_new=data.get('is_new', False),
        )

    @classmethod
    def from_db_row(cls, row: tuple, columns: List[str]) -> 'Paper':
        """从数据库行创建实例"""
        data = dict(zip(columns, row))
        return cls.from_dict(data)


@dataclass
class PaperHistory:
    """论文推送历史记录"""
    arxiv_id: str
    create_date: datetime
    score: float = 0.0
    score_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'arxiv_id': self.arxiv_id,
            'create_date': self.create_date,
            'score': self.score,
            'score_reason': self.score_reason,
        }
