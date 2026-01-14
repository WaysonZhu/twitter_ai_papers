"""
统一定时调度器
使用 APScheduler 实现三个独立的定时任务
"""
import logging
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from utils.logging_config import configure_root_logger
from services.fetch_service import fetch_service
from services.update_service import update_service
from services.push_service import push_service

# 配置日志（同时输出到控制台和文件）
configure_root_logger()
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler()


def parse_cron(cron_expr: str) -> CronTrigger:
    """解析 cron 表达式"""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError(f"无效的 cron 表达式: {cron_expr}")

    return CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )


def setup_scheduler():
    """配置定时任务"""

    # 任务1：增量抓取新论文
    if settings.FETCH_ENABLED:
        try:
            trigger = parse_cron(settings.FETCH_CRON)
            scheduler.add_job(
                fetch_service.run,
                trigger,
                id="fetch_papers",
                name="抓取 HF Trending 新论文",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] 增量抓取任务已配置: {settings.FETCH_CRON}")
        except Exception as e:
            logger.error(f"[Scheduler] 增量抓取任务配置失败: {e}")
    else:
        logger.info("[Scheduler] 增量抓取任务已禁用")

    # 任务2：更新已有论文指标
    if settings.UPDATE_ENABLED:
        try:
            trigger = parse_cron(settings.UPDATE_CRON)
            scheduler.add_job(
                update_service.run,
                trigger,
                id="update_metrics",
                name="更新论文指标",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] 更新指标任务已配置: {settings.UPDATE_CRON}")
        except Exception as e:
            logger.error(f"[Scheduler] 更新指标任务配置失败: {e}")
    else:
        logger.info("[Scheduler] 更新指标任务已禁用")

    # 任务3：GitHub 推送
    if settings.PUSH_ENABLED:
        try:
            trigger = parse_cron(settings.PUSH_CRON)
            scheduler.add_job(
                push_service.run,
                trigger,
                id="push_github",
                name="推送 TopK 到 GitHub",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] GitHub 推送任务已配置: {settings.PUSH_CRON}")
        except Exception as e:
            logger.error(f"[Scheduler] GitHub 推送任务配置失败: {e}")
    else:
        logger.info("[Scheduler] GitHub 推送任务已禁用")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("AI Papers Tracker - 定时调度器启动")
    logger.info("=" * 60)

    setup_scheduler()

    logger.info("[Scheduler] 调度器正在运行，按 Ctrl+C 停止...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("[Scheduler] 调度器已停止")


if __name__ == "__main__":
    main()
