-- AI Papers Tracker 数据库表结构
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_papers DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_papers;

-- 论文主表
CREATE TABLE IF NOT EXISTS everyday_ai_papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL COMMENT '抓取日期',
    arxiv_id VARCHAR(50) NOT NULL COMMENT 'ArXiv ID',
    display_order INT DEFAULT NULL COMMENT '显示顺序',
    title TEXT COMMENT '论文标题',
    url VARCHAR(500) COMMENT '论文链接',
    publication_date DATE COMMENT '发布日期',
    authors TEXT COMMENT '作者列表',
    type VARCHAR(50) COMMENT '论文类型',
    journal VARCHAR(200) COMMENT '期刊名称',

    -- 指标数据
    citation_count INT DEFAULT 0 COMMENT '引用数 (Semantic Scholar)',
    n_read INT DEFAULT 0 COMMENT '阅读数 (Mendeley)',
    x_num INT DEFAULT 0 COMMENT 'Twitter/X 提及数 (Altmetric)',
    cited_by_msm_count INT DEFAULT 0 COMMENT '主流媒体引用数 (Altmetric)',

    -- GitHub 数据
    github_url VARCHAR(500) COMMENT 'GitHub 仓库链接',
    star_num INT DEFAULT 0 COMMENT 'GitHub Stars',
    fork_num INT DEFAULT 0 COMMENT 'GitHub Forks',
    watch_num INT DEFAULT 0 COMMENT 'GitHub Watchers',

    -- 元数据
    from_source VARCHAR(50) DEFAULT 'HF_TRENDING' COMMENT '数据来源',
    is_new CHAR(1) DEFAULT '0' COMMENT '是否新论文',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引和约束（每篇论文只存一条，以 arxiv_id 为唯一键）
    UNIQUE KEY uk_arxiv_id (arxiv_id),
    INDEX idx_date (date),
    INDEX idx_star_num (star_num),
    INDEX idx_citation_count (citation_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日AI论文数据表';

-- GitHub 推送历史表
CREATE TABLE IF NOT EXISTS history_github_papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    arxiv_id VARCHAR(50) NOT NULL COMMENT 'ArXiv ID',
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '推送时间',
    score FLOAT DEFAULT 0 COMMENT '评分',
    score_reason TEXT COMMENT '评分原因',

    -- 索引
    UNIQUE KEY uk_arxiv_id (arxiv_id),
    INDEX idx_create_date (create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='GitHub推送历史记录表';
