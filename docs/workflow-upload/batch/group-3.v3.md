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
      "table_name": "inf_bc_order_item",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 12600000,
      "primary_key": [],
      "columns": [
        {
          "name": "order_item_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "agreement_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "cust_order_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "item_sequence",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_order_item_agreement",
          "columns": [
            "agreement_id"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_cust_order",
          "columns": [
            "cust_order_id"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_sequence",
          "columns": [
            "item_sequence"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_order_item_id",
          "columns": [
            "order_item_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `inf_bc_order_item` (\n  `order_item_id` bigint DEFAULT NULL,\n  `agreement_id` bigint DEFAULT NULL,\n  `cust_order_id` bigint DEFAULT NULL,\n  `item_sequence` bigint DEFAULT NULL,\n  KEY `idx_order_item_agreement` (`agreement_id`),\n  KEY `idx_order_item_cust_order` (`cust_order_id`),\n  KEY `idx_order_item_sequence` (`item_sequence`),\n  KEY `idx_order_item_order_item_id` (`order_item_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    },
    {
      "table_name": "inf_bc_tran_offer",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 980000,
      "primary_key": [],
      "columns": [
        {
          "name": "agreement_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "order_item_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "offer_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "prod_offer_inst_id",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_tran_offer_agreement",
          "columns": [
            "agreement_id"
          ],
          "unique": false
        },
        {
          "name": "idx_tran_offer_order_item",
          "columns": [
            "order_item_id"
          ],
          "unique": false
        },
        {
          "name": "idx_tran_offer_prod_offer_inst",
          "columns": [
            "prod_offer_inst_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `inf_bc_tran_offer` (\n  `agreement_id` bigint DEFAULT NULL,\n  `order_item_id` bigint DEFAULT NULL,\n  `offer_id` bigint DEFAULT NULL,\n  `prod_offer_inst_id` bigint DEFAULT NULL,\n  KEY `idx_tran_offer_agreement` (`agreement_id`),\n  KEY `idx_tran_offer_order_item` (`order_item_id`),\n  KEY `idx_tran_offer_prod_offer_inst` (`prod_offer_inst_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    }
  ]
}
```

## 权威表元数据摘要
### inf_bc_order_item
- table_name: inf_bc_order_item
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 12600000
- table_rows: 12600000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: order_item_id, cust_order_id
- index_count: 4
- has_indexes: yes
- index_names: idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence, idx_order_item_order_item_id
- ddl_available: yes
### inf_bc_tran_offer
- table_name: inf_bc_tran_offer
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 980000
- table_rows: 980000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_offer_inst_id, agreement_id
- index_count: 3
- has_indexes: yes
- index_names: idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst
- ddl_available: yes

## SQL 列表
### SQL 1
- sql_id: sql_5
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from inf_bc_order_item where agreement_id = ? and cust_order_id = ? order by item_sequence
- table_names: inf_bc_order_item
```sql
select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence
```
### SQL 2
- sql_id: sql_8
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = ? and order_item_id = ? order by prod_offer_inst_id
- table_names: inf_bc_tran_offer
```sql
select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id
```

## SQL 局部权威事实包
### sql_5 - order_item 多条件排序
- 原始 SQL：`select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence`
- 涉及表：inf_bc_order_item
- 本 SQL 必须至少引用这些索引名：idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_5",
  "required_index_names": [
    "idx_order_item_agreement",
    "idx_order_item_cust_order",
    "idx_order_item_sequence"
  ],
  "tables": [
    {
      "table_name": "inf_bc_order_item",
      "table_rows_exact": 12600000,
      "table_rows": 12600000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_order_item_agreement",
          "columns": [
            "agreement_id"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_cust_order",
          "columns": [
            "cust_order_id"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_sequence",
          "columns": [
            "item_sequence"
          ],
          "unique": false
        },
        {
          "name": "idx_order_item_order_item_id",
          "columns": [
            "order_item_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "order_item_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "agreement_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "cust_order_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "item_sequence",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "order_item_id",
        "cust_order_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence
```

#### 观测统计
```json
{
  "cluster_count": 64,
  "min_query_time_ms": 320.0,
  "avg_query_time_ms": 1320.0,
  "max_query_time_ms": 5860.0,
  "latest_timestamp": "2026-03-18 18:15:00"
}
```

#### 表 inf_bc_order_item 的局部权威事实
- table_rows_exact: 12600000
- table_rows: 12600000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: order_item_id, cust_order_id
- indexes: idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence, idx_order_item_order_item_id
- columns: order_item_id, agreement_id, cust_order_id, item_sequence

#### 表 inf_bc_order_item 的事实回显模板
- required_output_fact_line: table_name=inf_bc_order_item; table_rows=12600000; primary_key_only=NONE; required_index_names=idx_order_item_agreement,idx_order_item_cust_order,idx_order_item_sequence,idx_order_item_order_item_id

#### 表 inf_bc_order_item 的 DDL 摘要
```sql
CREATE TABLE `inf_bc_order_item` (
  `order_item_id` bigint DEFAULT NULL,
  `agreement_id` bigint DEFAULT NULL,
  `cust_order_id` bigint DEFAULT NULL,
  `item_sequence` bigint DEFAULT NULL,
  KEY `idx_order_item_agreement` (`agreement_id`),
  KEY `idx_order_item_cust_order` (`cust_order_id`),
  KEY `idx_order_item_sequence` (`item_sequence`),
  KEY `idx_order_item_order_item_id` (`order_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 inf_bc_order_item 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 12600000 引用，不得改写。
- 本表未提供主键信息，禁止把 [order_item_id, cust_order_id] 等字段写成主键。
- 索引已提供：idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence, idx_order_item_order_item_id。不得写成无索引或索引未知。

#### 表 inf_bc_order_item 的强制事实声明
- inf_bc_order_item 的 table_rows 和 table_rows_exact 都是 12600000，不是 0。
- inf_bc_order_item 的主键只有 NONE。
- inf_bc_order_item 的非主键字段包括 order_item_id, cust_order_id。
- inf_bc_order_item 已提供索引：idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence, idx_order_item_order_item_id。
### sql_8 - tran_offer 去重排序
- 原始 SQL：`select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id`
- 涉及表：inf_bc_tran_offer
- 本 SQL 必须至少引用这些索引名：idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_8",
  "required_index_names": [
    "idx_tran_offer_agreement",
    "idx_tran_offer_order_item",
    "idx_tran_offer_prod_offer_inst"
  ],
  "tables": [
    {
      "table_name": "inf_bc_tran_offer",
      "table_rows_exact": 980000,
      "table_rows": 980000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_tran_offer_agreement",
          "columns": [
            "agreement_id"
          ],
          "unique": false
        },
        {
          "name": "idx_tran_offer_order_item",
          "columns": [
            "order_item_id"
          ],
          "unique": false
        },
        {
          "name": "idx_tran_offer_prod_offer_inst",
          "columns": [
            "prod_offer_inst_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "agreement_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "order_item_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "offer_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "prod_offer_inst_id",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "prod_offer_inst_id",
        "agreement_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id
```

#### 观测统计
```json
{
  "cluster_count": 19,
  "min_query_time_ms": 95.0,
  "avg_query_time_ms": 510.0,
  "max_query_time_ms": 1490.0,
  "latest_timestamp": "2026-03-18 18:27:00"
}
```

#### 表 inf_bc_tran_offer 的局部权威事实
- table_rows_exact: 980000
- table_rows: 980000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_offer_inst_id, agreement_id
- indexes: idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst
- columns: agreement_id, order_item_id, offer_id, prod_offer_inst_id

#### 表 inf_bc_tran_offer 的事实回显模板
- required_output_fact_line: table_name=inf_bc_tran_offer; table_rows=980000; primary_key_only=NONE; required_index_names=idx_tran_offer_agreement,idx_tran_offer_order_item,idx_tran_offer_prod_offer_inst

#### 表 inf_bc_tran_offer 的 DDL 摘要
```sql
CREATE TABLE `inf_bc_tran_offer` (
  `agreement_id` bigint DEFAULT NULL,
  `order_item_id` bigint DEFAULT NULL,
  `offer_id` bigint DEFAULT NULL,
  `prod_offer_inst_id` bigint DEFAULT NULL,
  KEY `idx_tran_offer_agreement` (`agreement_id`),
  KEY `idx_tran_offer_order_item` (`order_item_id`),
  KEY `idx_tran_offer_prod_offer_inst` (`prod_offer_inst_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 inf_bc_tran_offer 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 980000 引用，不得改写。
- 本表未提供主键信息，禁止把 [prod_offer_inst_id, agreement_id] 等字段写成主键。
- 索引已提供：idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst。不得写成无索引或索引未知。

#### 表 inf_bc_tran_offer 的强制事实声明
- inf_bc_tran_offer 的 table_rows 和 table_rows_exact 都是 980000，不是 0。
- inf_bc_tran_offer 的主键只有 NONE。
- inf_bc_tran_offer 的非主键字段包括 prod_offer_inst_id, agreement_id。
- inf_bc_tran_offer 已提供索引：idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst。

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 64
- min_query_time_ms: 320.0
- avg_query_time_ms: 1320.0
- max_query_time_ms: 5860.0
- latest_timestamp: 2026-03-18 18:15:00
```sql
select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence
```
### 观测项 2
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 19
- min_query_time_ms: 95.0
- avg_query_time_ms: 510.0
- max_query_time_ms: 1490.0
- latest_timestamp: 2026-03-18 18:27:00
```sql
select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id
```

## 原始 DDL 附录

### inf_bc_order_item

```sql
CREATE TABLE `inf_bc_order_item` (
  `order_item_id` bigint DEFAULT NULL,
  `agreement_id` bigint DEFAULT NULL,
  `cust_order_id` bigint DEFAULT NULL,
  `item_sequence` bigint DEFAULT NULL,
  KEY `idx_order_item_agreement` (`agreement_id`),
  KEY `idx_order_item_cust_order` (`cust_order_id`),
  KEY `idx_order_item_sequence` (`item_sequence`),
  KEY `idx_order_item_order_item_id` (`order_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

### inf_bc_tran_offer

```sql
CREATE TABLE `inf_bc_tran_offer` (
  `agreement_id` bigint DEFAULT NULL,
  `order_item_id` bigint DEFAULT NULL,
  `offer_id` bigint DEFAULT NULL,
  `prod_offer_inst_id` bigint DEFAULT NULL,
  KEY `idx_tran_offer_agreement` (`agreement_id`),
  KEY `idx_tran_offer_order_item` (`order_item_id`),
  KEY `idx_tran_offer_prod_offer_inst` (`prod_offer_inst_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
