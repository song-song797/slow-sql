# 慢 SQL 分析输入文档

- 版本：V3
- 上传策略：短文聚焦上传
- SQL 数量：2

## 分析规则
- 只允许依据 AUTHORIZED_METADATA_JSON 和 LOCAL_FACT_PACKET_JSON 判断表结构、主键、索引、表行数和 DDL。
- 若 indexes 非空，禁止输出“无索引”“索引未知”“未显示索引信息”或同义表达。
- 若 table_rows_exact 为数值，禁止改写为 0、未知、空值或忽略不提。
- 若 ddl 已提供，禁止输出“DDL 未提供”“DDL 为空”或同义表达。
- 若 primary_key 非空，禁止把其他字段写成主键；若 primary_key 为空，禁止自行猜测主键。
- 每条 SQL 必须先回显输入事实，再给出性能判断。
- 若输入事实与经验推断冲突，优先以输入事实为准，并明确写出“输入事实如此提供”。
- 若认为现有索引不匹配当前 SQL，只能写“现有索引不匹配”，不得否认索引存在。

## 数据库连接信息
- mysql://127.0.0.1:3306/CUSDBX

## AUTHORIZED_METADATA_JSON
```json
{
  "tables": [
    {
      "table_name": "audit_log",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 8600000,
      "primary_key": [
        "id"
      ],
      "columns": [
        {
          "name": "id",
          "data_type": "bigint",
          "nullable": false
        },
        {
          "name": "user_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "request_path",
          "data_type": "varchar(255)",
          "nullable": true
        },
        {
          "name": "created_at",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "PRIMARY",
          "columns": [
            "id"
          ],
          "unique": true
        },
        {
          "name": "idx_audit_log_user_id",
          "columns": [
            "user_id"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_created_at",
          "columns": [
            "created_at"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_request_path",
          "columns": [
            "request_path"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_user_time",
          "columns": [
            "user_id",
            "created_at"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `audit_log` (\n  `id` bigint NOT NULL,\n  `user_id` bigint DEFAULT NULL,\n  `request_path` varchar(255) DEFAULT NULL,\n  `created_at` datetime DEFAULT NULL,\n  PRIMARY KEY (`id`),\n  KEY `idx_audit_log_user_id` (`user_id`),\n  KEY `idx_audit_log_created_at` (`created_at`),\n  KEY `idx_audit_log_request_path` (`request_path`),\n  KEY `idx_audit_log_user_time` (`user_id`,`created_at`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    }
  ]
}
```

## 权威表元数据摘要
### audit_log
- table_name: audit_log
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 8600000
- table_rows: 8600000
- primary_key: ['id']
- primary_key_only: id
- not_primary_key_columns: user_id, request_path
- index_count: 5
- has_indexes: yes
- index_names: PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time
- ddl_available: yes

## SQL 列表
### SQL 1
- sql_id: sql_9
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from audit_log where user_id = ? order by created_at desc limit ?
- table_names: audit_log
```sql
select * from audit_log where user_id = 10001 order by created_at desc limit 100
```
### SQL 2
- sql_id: sql_10
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select count(*) as total_count from audit_log where created_at >= ? and created_at < ? and request_path like ?
- table_names: audit_log
```sql
select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'
```

## SQL 局部权威事实包
### sql_9 - audit_log 用户维度查询
- 原始 SQL：`select * from audit_log where user_id = 10001 order by created_at desc limit 100`
- 涉及表：audit_log
- 本 SQL 必须至少引用这些索引名：PRIMARY, idx_audit_log_user_id, idx_audit_log_user_time, idx_audit_log_created_at

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_9",
  "required_index_names": [
    "PRIMARY",
    "idx_audit_log_user_id",
    "idx_audit_log_user_time",
    "idx_audit_log_created_at"
  ],
  "tables": [
    {
      "table_name": "audit_log",
      "table_rows_exact": 8600000,
      "table_rows": 8600000,
      "primary_key": [
        "id"
      ],
      "primary_key_only": [
        "id"
      ],
      "indexes": [
        {
          "name": "PRIMARY",
          "columns": [
            "id"
          ],
          "unique": true
        },
        {
          "name": "idx_audit_log_user_id",
          "columns": [
            "user_id"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_created_at",
          "columns": [
            "created_at"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_request_path",
          "columns": [
            "request_path"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_user_time",
          "columns": [
            "user_id",
            "created_at"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "id",
          "data_type": "bigint",
          "nullable": false
        },
        {
          "name": "user_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "request_path",
          "data_type": "varchar(255)",
          "nullable": true
        },
        {
          "name": "created_at",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "user_id",
        "request_path"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select * from audit_log where user_id = 10001 order by created_at desc limit 100
```

#### 观测统计
```json
{
  "cluster_count": 86,
  "min_query_time_ms": 260.0,
  "avg_query_time_ms": 1410.0,
  "max_query_time_ms": 6230.0,
  "latest_timestamp": "2026-03-18 18:31:00"
}
```

#### 表 audit_log 的局部权威事实
- table_rows_exact: 8600000
- table_rows: 8600000
- primary_key: ['id']
- primary_key_only: id
- not_primary_key_columns: user_id, request_path
- indexes: PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time
- columns: id, user_id, request_path, created_at

#### 表 audit_log 的事实回显模板
- required_output_fact_line: table_name=audit_log; table_rows=8600000; primary_key_only=id; required_index_names=PRIMARY,idx_audit_log_user_id,idx_audit_log_created_at,idx_audit_log_request_path,idx_audit_log_user_time

#### 表 audit_log 的 DDL 摘要
```sql
CREATE TABLE `audit_log` (
  `id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `request_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_audit_log_user_id` (`user_id`),
  KEY `idx_audit_log_created_at` (`created_at`),
  KEY `idx_audit_log_request_path` (`request_path`),
  KEY `idx_audit_log_user_time` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 audit_log 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 8600000 引用，不得改写。
- 本表主键仅为 [id]，不得将其他字段视为主键。
- 索引已提供：PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time。不得写成无索引或索引未知。

#### 表 audit_log 的强制事实声明
- audit_log 的 table_rows 和 table_rows_exact 都是 8600000，不是 0。
- audit_log 的主键只有 id。
- audit_log 的非主键字段包括 user_id, request_path。
- audit_log 已提供索引：PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time。
### sql_10 - audit_log 范围聚合
- 原始 SQL：`select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'`
- 涉及表：audit_log
- 本 SQL 必须至少引用这些索引名：PRIMARY, idx_audit_log_created_at, idx_audit_log_request_path

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_10",
  "required_index_names": [
    "PRIMARY",
    "idx_audit_log_created_at",
    "idx_audit_log_request_path"
  ],
  "tables": [
    {
      "table_name": "audit_log",
      "table_rows_exact": 8600000,
      "table_rows": 8600000,
      "primary_key": [
        "id"
      ],
      "primary_key_only": [
        "id"
      ],
      "indexes": [
        {
          "name": "PRIMARY",
          "columns": [
            "id"
          ],
          "unique": true
        },
        {
          "name": "idx_audit_log_user_id",
          "columns": [
            "user_id"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_created_at",
          "columns": [
            "created_at"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_request_path",
          "columns": [
            "request_path"
          ],
          "unique": false
        },
        {
          "name": "idx_audit_log_user_time",
          "columns": [
            "user_id",
            "created_at"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "id",
          "data_type": "bigint",
          "nullable": false
        },
        {
          "name": "user_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "request_path",
          "data_type": "varchar(255)",
          "nullable": true
        },
        {
          "name": "created_at",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "user_id",
        "request_path"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'
```

#### 观测统计
```json
{
  "cluster_count": 14,
  "min_query_time_ms": 410.0,
  "avg_query_time_ms": 1860.0,
  "max_query_time_ms": 7120.0,
  "latest_timestamp": "2026-03-18 18:35:00"
}
```

#### 表 audit_log 的局部权威事实
- table_rows_exact: 8600000
- table_rows: 8600000
- primary_key: ['id']
- primary_key_only: id
- not_primary_key_columns: user_id, request_path
- indexes: PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time
- columns: id, user_id, request_path, created_at

#### 表 audit_log 的事实回显模板
- required_output_fact_line: table_name=audit_log; table_rows=8600000; primary_key_only=id; required_index_names=PRIMARY,idx_audit_log_user_id,idx_audit_log_created_at,idx_audit_log_request_path,idx_audit_log_user_time

#### 表 audit_log 的 DDL 摘要
```sql
CREATE TABLE `audit_log` (
  `id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `request_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_audit_log_user_id` (`user_id`),
  KEY `idx_audit_log_created_at` (`created_at`),
  KEY `idx_audit_log_request_path` (`request_path`),
  KEY `idx_audit_log_user_time` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 audit_log 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 8600000 引用，不得改写。
- 本表主键仅为 [id]，不得将其他字段视为主键。
- 索引已提供：PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time。不得写成无索引或索引未知。

#### 表 audit_log 的强制事实声明
- audit_log 的 table_rows 和 table_rows_exact 都是 8600000，不是 0。
- audit_log 的主键只有 id。
- audit_log 的非主键字段包括 user_id, request_path。
- audit_log 已提供索引：PRIMARY, idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time。

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 86
- min_query_time_ms: 260.0
- avg_query_time_ms: 1410.0
- max_query_time_ms: 6230.0
- latest_timestamp: 2026-03-18 18:31:00
```sql
select * from audit_log where user_id = 10001 order by created_at desc limit 100
```
### 观测项 2
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 14
- min_query_time_ms: 410.0
- avg_query_time_ms: 1860.0
- max_query_time_ms: 7120.0
- latest_timestamp: 2026-03-18 18:35:00
```sql
select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'
```

## 原始 DDL 附录

### audit_log

```sql
CREATE TABLE `audit_log` (
  `id` bigint NOT NULL,
  `user_id` bigint DEFAULT NULL,
  `request_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_audit_log_user_id` (`user_id`),
  KEY `idx_audit_log_created_at` (`created_at`),
  KEY `idx_audit_log_request_path` (`request_path`),
  KEY `idx_audit_log_user_time` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
