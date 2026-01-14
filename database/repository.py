"""
数据库操作仓库
提供论文数据的 CRUD 操作
"""
import logging
from datetime import date, datetime
from typing import List, Optional, Set

from models.paper import Paper, PaperHistory
from database.connection import db

logger = logging.getLogger(__name__)


class PaperRepository:
    """论文数据仓库"""

    def get_existing_arxiv_ids(self) -> Set[str]:
        """获取所有已存在的 arxiv_id"""
        with db.cursor() as cursor:
            cursor.execute("SELECT DISTINCT arxiv_id FROM everyday_ai_papers")
            rows = cursor.fetchall()
            return {row['arxiv_id'] for row in rows}

    def get_pushed_arxiv_ids(self) -> Set[str]:
        """获取已推送到 GitHub 的 arxiv_id"""
        with db.cursor() as cursor:
            cursor.execute("SELECT arxiv_id FROM history_github_papers")
            rows = cursor.fetchall()
            return {row['arxiv_id'] for row in rows}

    def get_all_papers(self) -> List[Paper]:
        """获取所有论文"""
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM everyday_ai_papers
                ORDER BY date DESC, display_order ASC
            """)
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def get_papers_for_update(self, limit: int = 100) -> List[Paper]:
        """
        获取最久未更新的论文（用于滚动更新）
        按 update_time 升序，NULL 优先
        """
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM everyday_ai_papers
                ORDER BY update_time IS NULL DESC, update_time ASC
                LIMIT %s
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def get_total_paper_count(self) -> int:
        """获取论文总数"""
        with db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM everyday_ai_papers")
            row = cursor.fetchone()
            return row['cnt'] if row else 0

    def get_papers_by_date(self, target_date: date) -> List[Paper]:
        """获取指定日期的论文"""
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM everyday_ai_papers WHERE date = %s ORDER BY display_order ASC",
                (target_date,)
            )
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def get_unpushed_papers(self) -> List[Paper]:
        """获取未推送过的论文"""
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM everyday_ai_papers
                WHERE arxiv_id NOT IN (SELECT arxiv_id FROM history_github_papers)
            """)
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def get_today_pushed_count(self) -> int:
        """获取当天已推送的论文数量"""
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM history_github_papers
                WHERE DATE(create_date) = CURDATE()
            """)
            row = cursor.fetchone()
            return row['cnt'] if row else 0

    def get_papers_for_history(self, days: int = 5) -> List[Paper]:
        """获取最近 N 天推送过的论文"""
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT e.*, h.create_date AS push_date
                FROM everyday_ai_papers e
                INNER JOIN history_github_papers h ON e.arxiv_id = h.arxiv_id
                WHERE h.create_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY h.create_date DESC
            """, (days,))
            rows = cursor.fetchall()
            return [self._row_to_paper(row) for row in rows]

    def insert_paper(self, paper: Paper) -> bool:
        """插入单篇论文"""
        return self.insert_papers([paper])

    def insert_papers(self, papers: List[Paper]) -> bool:
        """批量插入论文（使用 ON DUPLICATE KEY UPDATE）"""
        if not papers:
            return True

        sql = """
        INSERT INTO everyday_ai_papers (
            date, arxiv_id, display_order, title, url, publication_date, authors,
            type, journal, citation_count, n_read, x_num, github_url,
            star_num, fork_num, watch_num, cited_by_msm_count,
            create_time, update_time, is_new, from_source
        ) VALUES (
            %(date)s, %(arxiv_id)s, %(display_order)s, %(title)s, %(url)s,
            %(publication_date)s, %(authors)s, %(type)s, %(journal)s,
            %(citation_count)s, %(n_read)s, %(x_num)s, %(github_url)s,
            %(star_num)s, %(fork_num)s, %(watch_num)s, %(cited_by_msm_count)s,
            %(create_time)s, %(update_time)s, %(is_new)s, %(from_source)s
        )
        ON DUPLICATE KEY UPDATE
            display_order = VALUES(display_order),
            title = VALUES(title),
            url = VALUES(url),
            publication_date = VALUES(publication_date),
            authors = VALUES(authors),
            type = VALUES(type),
            journal = VALUES(journal),
            citation_count = VALUES(citation_count),
            n_read = VALUES(n_read),
            x_num = VALUES(x_num),
            github_url = COALESCE(VALUES(github_url), github_url),
            star_num = VALUES(star_num),
            fork_num = VALUES(fork_num),
            watch_num = VALUES(watch_num),
            cited_by_msm_count = VALUES(cited_by_msm_count),
            update_time = NOW(),
            is_new = VALUES(is_new),
            from_source = VALUES(from_source)
        """

        try:
            with db.cursor() as cursor:
                for paper in papers:
                    data = self._paper_to_dict(paper)
                    cursor.execute(sql, data)

            logger.info(f"成功插入/更新 {len(papers)} 篇论文")
            return True

        except Exception as e:
            logger.error(f"插入论文失败: {e}")
            return False

    def update_paper_metrics(self, paper: Paper) -> bool:
        """更新论文的指标数据"""
        sql = """
        UPDATE everyday_ai_papers SET
            citation_count = %s,
            n_read = %s,
            x_num = %s,
            cited_by_msm_count = %s,
            star_num = %s,
            fork_num = %s,
            watch_num = %s,
            github_url = COALESCE(%s, github_url),
            journal = COALESCE(%s, journal),
            update_time = NOW()
        WHERE arxiv_id = %s
        """

        try:
            with db.cursor() as cursor:
                cursor.execute(sql, (
                    paper.citation_count,
                    paper.reader_count,
                    paper.x_num,
                    paper.cited_by_msm_count,
                    paper.star_num,
                    paper.fork_num,
                    paper.watch_num,
                    paper.github_url,
                    paper.journal,
                    paper.arxiv_id,
                ))
            return True

        except Exception as e:
            logger.error(f"更新论文指标失败 {paper.arxiv_id}: {e}")
            return False

    def save_to_history(self, papers: List[Paper]) -> bool:
        """保存推送历史"""
        if not papers:
            return True

        sql = """
        INSERT INTO history_github_papers (arxiv_id, create_date, score, score_reason)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            score = VALUES(score),
            score_reason = VALUES(score_reason)
        """

        try:
            with db.cursor() as cursor:
                for paper in papers:
                    cursor.execute(sql, (
                        paper.arxiv_id,
                        datetime.now(),
                        paper.score,
                        str(paper.score_reasons),
                    ))

            logger.info(f"成功保存 {len(papers)} 条推送历史")
            return True

        except Exception as e:
            logger.error(f"保存推送历史失败: {e}")
            return False

    def _paper_to_dict(self, paper: Paper) -> dict:
        """将 Paper 对象转换为数据库插入所需的字典"""
        return {
            'date': date.today(),
            'arxiv_id': paper.arxiv_id,
            'display_order': paper.display_order,
            'title': paper.title,
            'url': paper.url,
            'publication_date': paper.pub_date,
            'authors': paper.authors,
            'type': None,
            'journal': paper.journal,
            'citation_count': paper.citation_count,
            'n_read': paper.reader_count,
            'x_num': paper.x_num,
            'github_url': paper.github_url,
            'star_num': paper.star_num,
            'fork_num': paper.fork_num,
            'watch_num': paper.watch_num,
            'cited_by_msm_count': paper.cited_by_msm_count,
            'create_time': datetime.now(),
            'update_time': None,
            'is_new': '1' if paper.is_new else '0',
            'from_source': paper.from_source,
        }

    def _row_to_paper(self, row: dict) -> Paper:
        """将数据库行转换为 Paper 对象"""
        # 如果有 push_date（来自历史表查询），使用推送日期作为 create_time
        # 这样 README 按推送日期分组，而不是论文原始创建时间
        create_time = row.get('push_date') if 'push_date' in row else row.get('create_time')
        return Paper(
            arxiv_id=row.get('arxiv_id', ''),
            title=row.get('title', ''),
            authors=row.get('authors', ''),
            pub_date=row.get('publication_date'),
            url=row.get('url', ''),
            github_url=row.get('github_url'),
            star_num=row.get('star_num', 0) or 0,
            fork_num=row.get('fork_num', 0) or 0,
            watch_num=row.get('watch_num', 0) or 0,
            reader_count=row.get('n_read', 0) or 0,
            journal=row.get('journal'),
            x_num=row.get('x_num', 0) or 0,
            cited_by_msm_count=row.get('cited_by_msm_count', 0) or 0,
            citation_count=row.get('citation_count', 0) or 0,
            from_source=row.get('from_source', 'HF_TRENDING'),
            display_order=row.get('display_order'),
            is_new=row.get('is_new') == '1',
            create_time=create_time,
            update_time=row.get('update_time'),
        )


# 全局仓库实例
paper_repo = PaperRepository()
