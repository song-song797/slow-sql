USE slow_sql_db;

CREATE TABLE IF NOT EXISTS analysis_task (
    task_id VARCHAR(36) PRIMARY KEY COMMENT '任务ID(UUID)',
    status ENUM('pending', 'completed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    report_url VARCHAR(512) NULL COMMENT '报告下载链接',
    sql_text LONGTEXT NULL COMMENT '拼接后的SQL文本',
    analysis_context_json LONGTEXT NULL COMMENT '结构化分析上下文(JSON)',
    analysis_result_json LONGTEXT NULL COMMENT '结构化分析结果(JSON)',
    error_message LONGTEXT NULL COMMENT '失败原因',
    risk_level INT NULL DEFAULT 3 COMMENT '风险等级：1-低风险，2-中风险，3-高风险',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    finished_at TIMESTAMP NULL DEFAULT NULL COMMENT '完成/失败时间'
);

CREATE TABLE IF NOT EXISTS database_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    db_type VARCHAR(32) NULL COMMENT '数据库类型(mysql/postgresql)',
    db_name VARCHAR(64) NULL COMMENT '数据库名',
    db_desc VARCHAR(255) NULL COMMENT '数据库描述',
    db_ip VARCHAR(32) NULL COMMENT '数据库IP',
    db_port BIGINT NULL COMMENT '数据库端口',
    db_version VARCHAR(128) NULL COMMENT '数据库版本',
    table_name VARCHAR(128) NULL COMMENT '表名',
    table_desc VARCHAR(255) NULL COMMENT '表描述',
    table_rows BIGINT NULL COMMENT '表总行数',
    ddl TEXT NULL COMMENT '表结构DDL'
);

INSERT INTO database_info (
    db_type,
    db_name,
    db_desc,
    db_ip,
    db_port,
    db_version,
    table_name,
    table_desc,
    table_rows,
    ddl
)
SELECT
    'mysql',
    'slow_sql_db',
    '本地演示数据库',
    '127.0.0.1',
    3307,
    '8.0',
    'orders',
    '订单表',
    1024,
    'CREATE TABLE orders (id BIGINT PRIMARY KEY, user_id BIGINT, amount DECIMAL(10,2), created_at TIMESTAMP);'
WHERE NOT EXISTS (
    SELECT 1
    FROM database_info
    WHERE db_type = 'mysql' AND db_name = 'slow_sql_db' AND table_name = 'orders'
);
