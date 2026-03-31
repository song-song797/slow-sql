# 慢 SQL 分析输入文档

- 版本：V2
- 上传策略：集中上传
- SQL 数量：10

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
    },
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
    },
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
    },
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
- sql_id: sql_1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- template_sql: select * from account where acct_id = ?
- table_names: account
```sql
select * from account where acct_id = 1
```
### SQL 2
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
### SQL 3
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
### SQL 4
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
### SQL 5
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
### SQL 6
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
### SQL 7
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
### SQL 8
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
### SQL 9
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
### SQL 10
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
### sql_1 - account 等值查询
- 原始 SQL：`select * from account where acct_id = 1`
- 涉及表：account
- 本 SQL 必须至少引用这些索引名：idx_account_acct_id, idx_account_acct_id_cust_id

#### LOCAL_FACT_PACKET_JSON
```json
{
  "sql_id": "sql_1",
  "required_index_names": [
    "idx_account_acct_id",
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
select * from account where acct_id = 1
```

#### 观测统计
```json
{
  "cluster_count": 12,
  "min_query_time_ms": 120.0,
  "avg_query_time_ms": 560.0,
  "max_query_time_ms": 2100.0,
  "latest_timestamp": "2026-03-18 18:00:00"
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

## SQL 观测统计
### 观测项 1
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- cluster_count: 12
- min_query_time_ms: 120.0
- avg_query_time_ms: 560.0
- max_query_time_ms: 2100.0
- latest_timestamp: 2026-03-18 18:00:00
```sql
select * from account where acct_id = 1
```
### 观测项 2
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
### 观测项 3
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
### 观测项 4
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
### 观测项 5
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
### 观测项 6
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
### 观测项 7
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
### 观测项 8
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
### 观测项 9
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
### 观测项 10
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
