"""
清理历史数据脚本
修复之前的错误逻辑：每天只保留评分最高的 TOPK_COUNT 篇论文
"""
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from database.connection import db
from services.push_service import push_service
from utils.logging_config import configure_root_logger

configure_root_logger()

import logging
logger = logging.getLogger(__name__)


def cleanup_history():
    """清理历史数据，每天只保留 TOPK_COUNT 篇"""
    topk = settings.TOPK_COUNT
    logger.info(f"开始清理历史数据，每天只保留 {topk} 篇")

    with db.cursor() as cursor:
        # 1. 获取所有有推送记录的日期
        cursor.execute("""
            SELECT DATE(create_date) as push_date, COUNT(*) as cnt
            FROM history_github_papers
            GROUP BY DATE(create_date)
            ORDER BY push_date DESC
        """)
        dates = cursor.fetchall()

        logger.info(f"共有 {len(dates)} 天的推送记录")

        total_deleted = 0
        for row in dates:
            push_date = row['push_date']
            cnt = row['cnt']

            if cnt > topk:
                logger.info(f"  {push_date}: {cnt} 篇 -> 需要删除 {cnt - topk} 篇")

                # 获取该日期评分最高的 TOPK_COUNT 篇的 arxiv_id
                cursor.execute("""
                    SELECT arxiv_id FROM history_github_papers
                    WHERE DATE(create_date) = %s
                    ORDER BY score DESC
                    LIMIT %s
                """, (push_date, topk))
                top_ids = [r['arxiv_id'] for r in cursor.fetchall()]

                if top_ids:
                    # 删除不在 top_ids 中的记录
                    placeholders = ','.join(['%s'] * len(top_ids))
                    cursor.execute(f"""
                        DELETE FROM history_github_papers
                        WHERE DATE(create_date) = %s
                        AND arxiv_id NOT IN ({placeholders})
                    """, [push_date] + top_ids)

                    deleted = cursor.rowcount
                    total_deleted += deleted
                    logger.info(f"    已删除 {deleted} 条记录")
            else:
                logger.info(f"  {push_date}: {cnt} 篇 -> 正常")

        logger.info(f"清理完成，共删除 {total_deleted} 条记录")


def regenerate_readme():
    """重新生成并推送 README"""
    logger.info("重新生成 README 和 history...")

    # 强制重新生成（绕过当天已推送检查）
    # 直接调用内部方法更新页面
    from database.repository import paper_repo

    # 获取最近5天的历史论文
    history_papers = paper_repo.get_papers_for_history(days=settings.HISTORY_DAYS)

    if not history_papers:
        logger.warning("没有历史论文")
        return

    logger.info(f"获取到 {len(history_papers)} 篇历史论文")

    # 生成首页 README
    readme_content = push_service._generate_readme(history_papers)
    if readme_content:
        success = push_service._push_to_github(readme_content, is_history=False)
        if success:
            logger.info("首页 README 更新成功")
        else:
            logger.error("首页 README 更新失败")

    # 更新历史页面
    push_service._update_history_page()
    logger.info("历史页面更新完成")


if __name__ == "__main__":
    print("=" * 60)
    print("历史数据清理脚本")
    print("=" * 60)

    # 步骤1: 清理历史数据
    cleanup_history()

    print()

    # 步骤2: 重新生成 README
    regenerate_readme()

    print()
    print("=" * 60)
    print("清理完成!")
    print("=" * 60)
