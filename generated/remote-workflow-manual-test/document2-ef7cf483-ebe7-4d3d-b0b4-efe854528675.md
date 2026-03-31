# 慢 SQL 分析输入文档

## 分析规则
- 以下“权威表元数据摘要”来自本地元数据缓存或数据源补拉结果，优先级高于模型自行推测。
- 若 table_rows_exact 为数值，禁止改写为 0、未知或空值。
- 若 index_count > 0 或 has_indexes = yes，禁止写成“索引为空”“无索引”或“无法确认是否有索引”。
- 若 ddl_available = yes，禁止写成“DDL 为空”或“未提供 DDL”。
- 若无法确认，请仅依据“元数据缺失说明”描述，不得凭空补默认值。

## 数据库连接信息
- mysql://127.0.0.1:3307/slow_sql_db

## 权威表元数据摘要
### employees_summary
- table_name: employees_summary
- db_type: mysql
- db_name: slow_sql_db
- db_ip: 127.0.0.1
- db_port: 3307
- table_rows_exact: 1
- index_count: 3
- has_indexes: yes
- index_names: PRIMARY, idx_employee_no, idx_department_name
- index_columns: PRIMARY(ID) | idx_employee_no(employee_no) | idx_department_name(department_name)
- column_count: 6
- key_columns_hint: ID
- ddl_available: yes
- db_version: 8.4.8
- column_definitions: ID bigint NOT NULL; employee_no varchar(32) NOT NULL; employee_name varchar(128) NOT NULL; department_name varchar(128) NULL; salary_total decimal(12 NULL; updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP

## SQL 列表
### SQL 1
- sql_id: sql_1
- db_type: mysql
- db_name: slow_sql_db
- db_ip: 127.0.0.1
- db_port: 3307
- template_sql: SELECT * FROM `slow_sql_db`.`employees_summary` WHERE `ID` = ?
- table_names: employees_summary
```sql
SELECT * FROM `slow_sql_db`.`employees_summary` WHERE `ID` = 1048563
```

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: slow_sql_db
- db_ip: 127.0.0.1
- cluster_count: 1
- min_query_time_ms: 12.3
- avg_query_time_ms: 12.3
- max_query_time_ms: 12.3
- latest_timestamp: -
```sql
SELECT * FROM `slow_sql_db`.`employees_summary` WHERE `ID` = 1048563
```

## 原始 DDL 附录
### employees_summary
```sql
CREATE TABLE `employees_summary` (
  `ID` bigint NOT NULL,
  `employee_no` varchar(32) NOT NULL,
  `employee_name` varchar(128) NOT NULL,
  `department_name` varchar(128) DEFAULT NULL,
  `salary_total` decimal(12,2) DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ID`),
  KEY `idx_employee_no` (`employee_no`),
  KEY `idx_department_name` (`department_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
