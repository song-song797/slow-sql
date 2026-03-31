# 慢 SQL 分析输入文档

- 版本：V3
- 上传策略：短文聚焦上传
- SQL 数量：3

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
      "table_name": "inf_bc_prod_inst",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 5200000,
      "primary_key": [],
      "columns": [
        {
          "name": "prod_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "owner_cust_id",
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
        },
        {
          "name": "last_order_item_id",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_prod_inst_owner_cust",
          "columns": [
            "owner_cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_order_item",
          "columns": [
            "last_order_item_id"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_status",
          "columns": [
            "status_cd",
            "update_date"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_prod_inst_id",
          "columns": [
            "prod_inst_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `inf_bc_prod_inst` (\n  `prod_inst_id` bigint DEFAULT NULL,\n  `owner_cust_id` bigint DEFAULT NULL,\n  `status_cd` varchar(64) DEFAULT NULL,\n  `update_date` datetime DEFAULT NULL,\n  `last_order_item_id` bigint DEFAULT NULL,\n  KEY `idx_prod_inst_owner_cust` (`owner_cust_id`),\n  KEY `idx_prod_inst_order_item` (`last_order_item_id`),\n  KEY `idx_prod_inst_status` (`status_cd`,`update_date`),\n  KEY `idx_prod_inst_prod_inst_id` (`prod_inst_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    },
    {
      "table_name": "inf_bc_prod_inst_acct_rel",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 6800000,
      "primary_key": [],
      "columns": [
        {
          "name": "prod_inst_acct_rel_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "acct_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "prod_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_piar_acct_id",
          "columns": [
            "acct_id"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_prod_inst_id",
          "columns": [
            "prod_inst_id"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_status",
          "columns": [
            "status_cd"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_agree_id",
          "columns": [
            "agree_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `inf_bc_prod_inst_acct_rel` (\n  `prod_inst_acct_rel_id` bigint DEFAULT NULL,\n  `acct_id` bigint DEFAULT NULL,\n  `prod_inst_id` bigint DEFAULT NULL,\n  `status_cd` varchar(64) DEFAULT NULL,\n  KEY `idx_piar_acct_id` (`acct_id`),\n  KEY `idx_piar_prod_inst_id` (`prod_inst_id`),\n  KEY `idx_piar_status` (`status_cd`),\n  KEY `idx_piar_agree_id` (`agree_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    },
    {
      "table_name": "inf_bc_offer_inst",
      "db_type": "mysql",
      "db_name": "CUSDBX",
      "table_rows_exact": 4300000,
      "primary_key": [],
      "columns": [
        {
          "name": "offer_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "owner_cust_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        },
        {
          "name": "create_date",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "indexes": [
        {
          "name": "idx_offer_inst_owner_cust",
          "columns": [
            "owner_cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_offer_id",
          "columns": [
            "offer_id"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_status",
          "columns": [
            "status_cd",
            "create_date"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_order_item",
          "columns": [
            "last_order_item_id"
          ],
          "unique": false
        }
      ],
      "ddl": "CREATE TABLE `inf_bc_offer_inst` (\n  `offer_inst_id` bigint DEFAULT NULL,\n  `owner_cust_id` bigint DEFAULT NULL,\n  `status_cd` varchar(64) DEFAULT NULL,\n  `create_date` datetime DEFAULT NULL,\n  KEY `idx_offer_inst_owner_cust` (`owner_cust_id`),\n  KEY `idx_offer_inst_offer_id` (`offer_id`),\n  KEY `idx_offer_inst_status` (`status_cd`,`create_date`),\n  KEY `idx_offer_inst_order_item` (`last_order_item_id`)\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    }
  ]
}
```

## 权威表元数据摘要
### inf_bc_prod_inst
- table_name: inf_bc_prod_inst
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 5200000
- table_rows: 5200000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_inst_id, owner_cust_id
- index_count: 4
- has_indexes: yes
- index_names: idx_prod_inst_owner_cust, idx_prod_inst_order_item, idx_prod_inst_status, idx_prod_inst_prod_inst_id
- ddl_available: yes
### inf_bc_prod_inst_acct_rel
- table_name: inf_bc_prod_inst_acct_rel
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 6800000
- table_rows: 6800000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_inst_acct_rel_id, acct_id
- index_count: 4
- has_indexes: yes
- index_names: idx_piar_acct_id, idx_piar_prod_inst_id, idx_piar_status, idx_piar_agree_id
- ddl_available: yes
### inf_bc_offer_inst
- table_name: inf_bc_offer_inst
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 4300000
- table_rows: 4300000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: offer_inst_id, owner_cust_id
- index_count: 4
- has_indexes: yes
- index_names: idx_offer_inst_owner_cust, idx_offer_inst_offer_id, idx_offer_inst_status, idx_offer_inst_order_item
- ddl_available: yes

## SQL 列表
### SQL 1
- sql_id: sql_4
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = ? order by update_date desc limit ?
- table_names: inf_bc_prod_inst
```sql
select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50
```
### SQL 2
- sql_id: sql_6
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from inf_bc_prod_inst_acct_rel where acct_id = ? and status_cd = ?
- table_names: inf_bc_prod_inst_acct_rel
```sql
select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'
```
### SQL 3
- sql_id: sql_7
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from inf_bc_offer_inst where owner_cust_id = ? and status_cd = ? order by create_date desc limit ?
- table_names: inf_bc_offer_inst
```sql
select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100
```

## SQL 局部权威事实包
### sql_4 - prod_inst 过滤排序分页
- 原始 SQL：`select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50`
- 涉及表：inf_bc_prod_inst
- 本 SQL 必须至少引用这些索引名：idx_prod_inst_owner_cust, idx_prod_inst_status

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_4",
  "required_index_names": [
    "idx_prod_inst_owner_cust",
    "idx_prod_inst_status"
  ],
  "tables": [
    {
      "table_name": "inf_bc_prod_inst",
      "table_rows_exact": 5200000,
      "table_rows": 5200000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_prod_inst_owner_cust",
          "columns": [
            "owner_cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_order_item",
          "columns": [
            "last_order_item_id"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_status",
          "columns": [
            "status_cd",
            "update_date"
          ],
          "unique": false
        },
        {
          "name": "idx_prod_inst_prod_inst_id",
          "columns": [
            "prod_inst_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "prod_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "owner_cust_id",
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
        },
        {
          "name": "last_order_item_id",
          "data_type": "bigint",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "prod_inst_id",
        "owner_cust_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50
```

#### 观测统计
```json
{
  "cluster_count": 73,
  "min_query_time_ms": 210.0,
  "avg_query_time_ms": 980.0,
  "max_query_time_ms": 4210.0,
  "latest_timestamp": "2026-03-18 18:12:00"
}
```

#### 表 inf_bc_prod_inst 的局部权威事实
- table_rows_exact: 5200000
- table_rows: 5200000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_inst_id, owner_cust_id
- indexes: idx_prod_inst_owner_cust, idx_prod_inst_order_item, idx_prod_inst_status, idx_prod_inst_prod_inst_id
- columns: prod_inst_id, owner_cust_id, status_cd, update_date, last_order_item_id

#### 表 inf_bc_prod_inst 的事实回显模板
- required_output_fact_line: table_name=inf_bc_prod_inst; table_rows=5200000; primary_key_only=NONE; required_index_names=idx_prod_inst_owner_cust,idx_prod_inst_order_item,idx_prod_inst_status,idx_prod_inst_prod_inst_id

#### 表 inf_bc_prod_inst 的 DDL 摘要
```sql
CREATE TABLE `inf_bc_prod_inst` (
  `prod_inst_id` bigint DEFAULT NULL,
  `owner_cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `last_order_item_id` bigint DEFAULT NULL,
  KEY `idx_prod_inst_owner_cust` (`owner_cust_id`),
  KEY `idx_prod_inst_order_item` (`last_order_item_id`),
  KEY `idx_prod_inst_status` (`status_cd`,`update_date`),
  KEY `idx_prod_inst_prod_inst_id` (`prod_inst_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 inf_bc_prod_inst 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 5200000 引用，不得改写。
- 本表未提供主键信息，禁止把 [prod_inst_id, owner_cust_id] 等字段写成主键。
- 索引已提供：idx_prod_inst_owner_cust, idx_prod_inst_order_item, idx_prod_inst_status, idx_prod_inst_prod_inst_id。不得写成无索引或索引未知。

#### 表 inf_bc_prod_inst 的强制事实声明
- inf_bc_prod_inst 的 table_rows 和 table_rows_exact 都是 5200000，不是 0。
- inf_bc_prod_inst 的主键只有 NONE。
- inf_bc_prod_inst 的非主键字段包括 prod_inst_id, owner_cust_id。
- inf_bc_prod_inst 已提供索引：idx_prod_inst_owner_cust, idx_prod_inst_order_item, idx_prod_inst_status, idx_prod_inst_prod_inst_id。
### sql_6 - prod_inst_acct_rel 多条件过滤
- 原始 SQL：`select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'`
- 涉及表：inf_bc_prod_inst_acct_rel
- 本 SQL 必须至少引用这些索引名：idx_piar_acct_id, idx_piar_status

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_6",
  "required_index_names": [
    "idx_piar_acct_id",
    "idx_piar_status"
  ],
  "tables": [
    {
      "table_name": "inf_bc_prod_inst_acct_rel",
      "table_rows_exact": 6800000,
      "table_rows": 6800000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_piar_acct_id",
          "columns": [
            "acct_id"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_prod_inst_id",
          "columns": [
            "prod_inst_id"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_status",
          "columns": [
            "status_cd"
          ],
          "unique": false
        },
        {
          "name": "idx_piar_agree_id",
          "columns": [
            "agree_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "prod_inst_acct_rel_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "acct_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "prod_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "prod_inst_acct_rel_id",
        "acct_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'
```

#### 观测统计
```json
{
  "cluster_count": 22,
  "min_query_time_ms": 70.0,
  "avg_query_time_ms": 390.0,
  "max_query_time_ms": 1330.0,
  "latest_timestamp": "2026-03-18 18:19:00"
}
```

#### 表 inf_bc_prod_inst_acct_rel 的局部权威事实
- table_rows_exact: 6800000
- table_rows: 6800000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: prod_inst_acct_rel_id, acct_id
- indexes: idx_piar_acct_id, idx_piar_prod_inst_id, idx_piar_status, idx_piar_agree_id
- columns: prod_inst_acct_rel_id, acct_id, prod_inst_id, status_cd

#### 表 inf_bc_prod_inst_acct_rel 的事实回显模板
- required_output_fact_line: table_name=inf_bc_prod_inst_acct_rel; table_rows=6800000; primary_key_only=NONE; required_index_names=idx_piar_acct_id,idx_piar_prod_inst_id,idx_piar_status,idx_piar_agree_id

#### 表 inf_bc_prod_inst_acct_rel 的 DDL 摘要
```sql
CREATE TABLE `inf_bc_prod_inst_acct_rel` (
  `prod_inst_acct_rel_id` bigint DEFAULT NULL,
  `acct_id` bigint DEFAULT NULL,
  `prod_inst_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  KEY `idx_piar_acct_id` (`acct_id`),
  KEY `idx_piar_prod_inst_id` (`prod_inst_id`),
  KEY `idx_piar_status` (`status_cd`),
  KEY `idx_piar_agree_id` (`agree_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 inf_bc_prod_inst_acct_rel 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 6800000 引用，不得改写。
- 本表未提供主键信息，禁止把 [prod_inst_acct_rel_id, acct_id] 等字段写成主键。
- 索引已提供：idx_piar_acct_id, idx_piar_prod_inst_id, idx_piar_status, idx_piar_agree_id。不得写成无索引或索引未知。

#### 表 inf_bc_prod_inst_acct_rel 的强制事实声明
- inf_bc_prod_inst_acct_rel 的 table_rows 和 table_rows_exact 都是 6800000，不是 0。
- inf_bc_prod_inst_acct_rel 的主键只有 NONE。
- inf_bc_prod_inst_acct_rel 的非主键字段包括 prod_inst_acct_rel_id, acct_id。
- inf_bc_prod_inst_acct_rel 已提供索引：idx_piar_acct_id, idx_piar_prod_inst_id, idx_piar_status, idx_piar_agree_id。
### sql_7 - offer_inst 过滤排序分页
- 原始 SQL：`select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100`
- 涉及表：inf_bc_offer_inst
- 本 SQL 必须至少引用这些索引名：idx_offer_inst_owner_cust, idx_offer_inst_status

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_7",
  "required_index_names": [
    "idx_offer_inst_owner_cust",
    "idx_offer_inst_status"
  ],
  "tables": [
    {
      "table_name": "inf_bc_offer_inst",
      "table_rows_exact": 4300000,
      "table_rows": 4300000,
      "primary_key": [],
      "primary_key_only": [],
      "indexes": [
        {
          "name": "idx_offer_inst_owner_cust",
          "columns": [
            "owner_cust_id"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_offer_id",
          "columns": [
            "offer_id"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_status",
          "columns": [
            "status_cd",
            "create_date"
          ],
          "unique": false
        },
        {
          "name": "idx_offer_inst_order_item",
          "columns": [
            "last_order_item_id"
          ],
          "unique": false
        }
      ],
      "columns": [
        {
          "name": "offer_inst_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "owner_cust_id",
          "data_type": "bigint",
          "nullable": true
        },
        {
          "name": "status_cd",
          "data_type": "varchar(64)",
          "nullable": true
        },
        {
          "name": "create_date",
          "data_type": "datetime",
          "nullable": true
        }
      ],
      "forbidden_primary_key_columns": [
        "offer_inst_id",
        "owner_cust_id"
      ]
    }
  ]
}
```

#### SQL 文本
```sql
select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100
```

#### 观测统计
```json
{
  "cluster_count": 55,
  "min_query_time_ms": 150.0,
  "avg_query_time_ms": 760.0,
  "max_query_time_ms": 3180.0,
  "latest_timestamp": "2026-03-18 18:23:00"
}
```

#### 表 inf_bc_offer_inst 的局部权威事实
- table_rows_exact: 4300000
- table_rows: 4300000
- primary_key: []
- primary_key_only: NONE
- not_primary_key_columns: offer_inst_id, owner_cust_id
- indexes: idx_offer_inst_owner_cust, idx_offer_inst_offer_id, idx_offer_inst_status, idx_offer_inst_order_item
- columns: offer_inst_id, owner_cust_id, status_cd, create_date

#### 表 inf_bc_offer_inst 的事实回显模板
- required_output_fact_line: table_name=inf_bc_offer_inst; table_rows=4300000; primary_key_only=NONE; required_index_names=idx_offer_inst_owner_cust,idx_offer_inst_offer_id,idx_offer_inst_status,idx_offer_inst_order_item

#### 表 inf_bc_offer_inst 的 DDL 摘要
```sql
CREATE TABLE `inf_bc_offer_inst` (
  `offer_inst_id` bigint DEFAULT NULL,
  `owner_cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  KEY `idx_offer_inst_owner_cust` (`owner_cust_id`),
  KEY `idx_offer_inst_offer_id` (`offer_id`),
  KEY `idx_offer_inst_status` (`status_cd`,`create_date`),
  KEY `idx_offer_inst_order_item` (`last_order_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

#### 表 inf_bc_offer_inst 的本节分析约束
- table_rows_exact 与 table_rows 都必须按 4300000 引用，不得改写。
- 本表未提供主键信息，禁止把 [offer_inst_id, owner_cust_id] 等字段写成主键。
- 索引已提供：idx_offer_inst_owner_cust, idx_offer_inst_offer_id, idx_offer_inst_status, idx_offer_inst_order_item。不得写成无索引或索引未知。

#### 表 inf_bc_offer_inst 的强制事实声明
- inf_bc_offer_inst 的 table_rows 和 table_rows_exact 都是 4300000，不是 0。
- inf_bc_offer_inst 的主键只有 NONE。
- inf_bc_offer_inst 的非主键字段包括 offer_inst_id, owner_cust_id。
- inf_bc_offer_inst 已提供索引：idx_offer_inst_owner_cust, idx_offer_inst_offer_id, idx_offer_inst_status, idx_offer_inst_order_item。

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 73
- min_query_time_ms: 210.0
- avg_query_time_ms: 980.0
- max_query_time_ms: 4210.0
- latest_timestamp: 2026-03-18 18:12:00
```sql
select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50
```
### 观测项 2
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 22
- min_query_time_ms: 70.0
- avg_query_time_ms: 390.0
- max_query_time_ms: 1330.0
- latest_timestamp: 2026-03-18 18:19:00
```sql
select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'
```
### 观测项 3
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 55
- min_query_time_ms: 150.0
- avg_query_time_ms: 760.0
- max_query_time_ms: 3180.0
- latest_timestamp: 2026-03-18 18:23:00
```sql
select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100
```

## 原始 DDL 附录

### inf_bc_prod_inst

```sql
CREATE TABLE `inf_bc_prod_inst` (
  `prod_inst_id` bigint DEFAULT NULL,
  `owner_cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `last_order_item_id` bigint DEFAULT NULL,
  KEY `idx_prod_inst_owner_cust` (`owner_cust_id`),
  KEY `idx_prod_inst_order_item` (`last_order_item_id`),
  KEY `idx_prod_inst_status` (`status_cd`,`update_date`),
  KEY `idx_prod_inst_prod_inst_id` (`prod_inst_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

### inf_bc_prod_inst_acct_rel

```sql
CREATE TABLE `inf_bc_prod_inst_acct_rel` (
  `prod_inst_acct_rel_id` bigint DEFAULT NULL,
  `acct_id` bigint DEFAULT NULL,
  `prod_inst_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  KEY `idx_piar_acct_id` (`acct_id`),
  KEY `idx_piar_prod_inst_id` (`prod_inst_id`),
  KEY `idx_piar_status` (`status_cd`),
  KEY `idx_piar_agree_id` (`agree_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

### inf_bc_offer_inst

```sql
CREATE TABLE `inf_bc_offer_inst` (
  `offer_inst_id` bigint DEFAULT NULL,
  `owner_cust_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  KEY `idx_offer_inst_owner_cust` (`owner_cust_id`),
  KEY `idx_offer_inst_offer_id` (`offer_id`),
  KEY `idx_offer_inst_status` (`status_cd`,`create_date`),
  KEY `idx_offer_inst_order_item` (`last_order_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
