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
      "table_name": "customer",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 890000,
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
          "name": "region_id",
          "data_type": "bigint",
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
          "name": "idx_customer_cust_id",
          "columns": [
            "cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_customer_status_region",
          "columns": [
            "status_cd",
            "region_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `customer` (\n  `id` bigint NOT NULL,\n  `cust_id` bigint DEFAULT NULL,\n  `status_cd` varchar(64) DEFAULT NULL,\n  `region_id` bigint DEFAULT NULL,\n  PRIMARY KEY (`id`),\n  KEY `idx_customer_cust_id` (`cust_id`),\n  KEY `idx_customer_status_region` (`status_cd`,`region_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    }
  ]
}
```

## 权威表元数据摘要
### customer
- table_name: customer
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 890000
- table_rows: 890000
- primary_key: ['id']
- primary_key_only: id
- not_primary_key_columns: cust_id
- index_count: 3
- has_indexes: yes
- index_names: PRIMARY, idx_customer_cust_id, idx_customer_status_region
- ddl_available: yes

## SQL 列表
### SQL 1
- sql_id: sql_3
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from customer where cust_id = ?
- table_names: customer
```sql
select * from customer where cust_id = 20001
```

## SQL 局部权威事实包
### sql_3 - customer 高选择性等值查询
- 原始 SQL：`select * from customer where cust_id = 20001`
- 涉及表：customer
- 本 SQL 必须至少引用这些索引名：PRIMARY, idx_customer_cust_id

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_3",
  "required_index_names": [
    "PRIMARY",
    "idx_customer_cust_id"
  ],
  "tables": [
    {
      "table_name": "customer",
      "table_rows_exact": 890000,
      "table_rows": 890000,
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
          "name": "idx_customer_cust_id",
          "columns": [
            "cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_customer_status_region",
          "columns": [
            "status_cd",
            "region_id"
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
          "name": "region_id",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "cust_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select * from customer where cust_id = 20001
```

#### 观测统计
```json
{
  "cluster_count": 28,
  "min_query_time_ms": 40.0,
  "avg_query_time_ms": 170.0,
  "max_query_time_ms": 620.0,
  "latest_timestamp": "2026-03-18 18:09:00"
}
```

#### 表 customer 的局部权威事实
- table_rows_exact: 890000
- table_rows: 890000
- primary_key: ['id']
- primary_key_only: id
- not_primary_key_columns: cust_id
- indexes: PRIMARY, idx_customer_cust_id, idx_customer_status_region
- columns: id, cust_id, status_cd, region_id

#### 表 customer 的事实回显模板
- required_output_fact_line: table_name=customer; table_rows=890000; primary_key_only=id; required_index_names=PRIMARY,idx_customer_cust_id,idx_customer_status_region

#### 表 customer 的 DDL 摘要
```sql
CREATE TABLE `customer` (
  `id` bigint NOT NULL,
  `cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `region_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_customer_cust_id` (`cust_id`),
  KEY `idx_customer_status_region` (`status_cd`,`region_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 customer 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 890000 引用，不得改写。
- 本表主键仅为 [id]，不得将其他字段视为主键。
- 索引已提供：PRIMARY, idx_customer_cust_id, idx_customer_status_region。不得写成无索引或索引未知。

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 28
- min_query_time_ms: 40.0
- avg_query_time_ms: 170.0
- max_query_time_ms: 620.0
- latest_timestamp: 2026-03-18 18:09:00
```sql
select * from customer where cust_id = 20001
```

## 原始 DDL 附录

### customer

```sql
CREATE TABLE `customer` (
  `id` bigint NOT NULL,
  `cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `region_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_customer_cust_id` (`cust_id`),
  KEY `idx_customer_status_region` (`status_cd`,`region_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
