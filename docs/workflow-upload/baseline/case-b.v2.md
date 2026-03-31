# 慢 SQL 分析输入文档

- 版本：V2
- 上传策略：集中上传
- SQL 数量：1

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
      "table_name": "account",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 150000,
      "primary_key": [],
      "columns": [
        {
          "name": "acct_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "cust_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        },
        {
          "name": "update_date",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_account_acct_id_cust_id",
          "columns": [
            "acct_id",
            "cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_account_acct_id",
          "columns": [
            "acct_id"
          ],
          "unique": false
        },
        {
          "name": "idx_account_seq_nbr",
          "columns": [
            "seq_nbr"
          ],
          "unique": false
        },
        {
          "name": "idx_account_cust_id",
          "columns": [
            "cust_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `account` (\n  `acct_id` bigint DEFAULT NULL,\n  `cust_id` bigint DEFAULT NULL,\n  `status_cd` varchar(64) DEFAULT NULL,\n  `update_date` datetime DEFAULT NULL,\n  KEY `idx_account_acct_id_cust_id` (`acct_id`,`cust_id`),\n  KEY `idx_account_acct_id` (`acct_id`),\n  KEY `idx_account_seq_nbr` (`seq_nbr`),\n  KEY `idx_account_cust_id` (`cust_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    }
  ]
}
```

## 权威表元数据摘要
### account
- table_name: account
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 150000
- table_rows: 150000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: acct_id, cust_id
- index_count: 4
- has_indexes: yes
- index_names: idx_account_acct_id_cust_id, idx_account_acct_id, idx_account_seq_nbr, idx_account_cust_id
- ddl_available: yes

## SQL 列表
### SQL 1
- sql_id: sql_2
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select acct_id, cust_id, status_cd from account where cust_id = ? order by update_date desc limit ?
- table_names: account
```sql
select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20
```

## SQL 局部权威事实包
### sql_2 - account 过滤排序分页
- 原始 SQL：`select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20`
- 涉及表：account
- 本 SQL 必须至少引用这些索引名：idx_account_cust_id, idx_account_acct_id_cust_id

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_2",
  "required_index_names": [
    "idx_account_cust_id",
    "idx_account_acct_id_cust_id"
  ],
  "tables": [
    {
      "table_name": "account",
      "table_rows_exact": 150000,
      "table_rows": 150000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_account_acct_id_cust_id",
          "columns": [
            "acct_id",
            "cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_account_acct_id",
          "columns": [
            "acct_id"
          ],
          "unique": false
        },
        {
          "name": "idx_account_seq_nbr",
          "columns": [
            "seq_nbr"
          ],
          "unique": false
        },
        {
          "name": "idx_account_cust_id",
          "columns": [
            "cust_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "acct_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "cust_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        },
        {
          "name": "update_date",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "acct_id",
        "cust_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20
```

#### 观测统计
```json
{
  "cluster_count": 37,
  "min_query_time_ms": 85.0,
  "avg_query_time_ms": 430.0,
  "max_query_time_ms": 1860.0,
  "latest_timestamp": "2026-03-18 18:06:00"
}
```

#### 表 account 的局部权威事实
- table_rows_exact: 150000
- table_rows: 150000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: acct_id, cust_id
- indexes: idx_account_acct_id_cust_id, idx_account_acct_id, idx_account_seq_nbr, idx_account_cust_id
- columns: acct_id, cust_id, status_cd, update_date

#### 表 account 的事实回显模板
- required_output_fact_line: table_name=account; table_rows=150000; primary_key_only=NONE; required_index_names=idx_account_acct_id_cust_id,idx_account_acct_id,idx_account_seq_nbr,idx_account_cust_id

#### 表 account 的 DDL 摘要
```sql
CREATE TABLE `account` (
  `acct_id` bigint DEFAULT NULL,
  `cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  KEY `idx_account_acct_id_cust_id` (`acct_id`,`cust_id`),
  KEY `idx_account_acct_id` (`acct_id`),
  KEY `idx_account_seq_nbr` (`seq_nbr`),
  KEY `idx_account_cust_id` (`cust_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 account 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 150000 引用，不得改写。
- 本表未提供主键信息，禁止把 [acct_id, cust_id] 等字段写成主键。
- 索引已提供：idx_account_acct_id_cust_id, idx_account_acct_id, idx_account_seq_nbr, idx_account_cust_id。不得写成无索引或索引未知。

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 37
- min_query_time_ms: 85.0
- avg_query_time_ms: 430.0
- max_query_time_ms: 1860.0
- latest_timestamp: 2026-03-18 18:06:00
```sql
select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20
```

## 原始 DDL 附录

### account

```sql
CREATE TABLE `account` (
  `acct_id` bigint DEFAULT NULL,
  `cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  KEY `idx_account_acct_id_cust_id` (`acct_id`,`cust_id`),
  KEY `idx_account_acct_id` (`acct_id`),
  KEY `idx_account_seq_nbr` (`seq_nbr`),
  KEY `idx_account_cust_id` (`cust_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
