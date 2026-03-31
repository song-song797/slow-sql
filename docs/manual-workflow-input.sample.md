# 慢 SQL 分析输入文档

## 分析规则
- 以下“权威表元数据摘要”来自本地元数据缓存或数据源补拉结果，优先级高于模型自行推测。
- 若 table_rows_exact 为数值，禁止改写为 0、未知或空值。
- 若 index_count > 0 或 has_indexes = yes，禁止写成“索引为空”“无索引”或“无法确认是否有索引”。
- 若 ddl_available = yes，禁止写成“DDL 为空”或“未提供 DDL”。
- 若无法确认，请仅依据“元数据缺失说明”描述，不得凭空补默认值。

## 数据库连接信息
- mysql://127.0.0.1:3306/CUSDBX

## 权威表元数据摘要
### account
- table_name: account
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 150000
- index_count: 4
- has_indexes: yes
- index_names: idx_account_acct_id_cust_id, idx_account_acct_id, idx_account_seq_nbr, idx_account_cust_id
- index_columns: idx_account_acct_id_cust_id(acct_id,cust_id) | idx_account_acct_id(acct_id) | idx_account_seq_nbr(seq_nbr) | idx_account_cust_id(cust_id)
- column_count: 28
- key_columns_hint: acct_id, cust_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: acct_id bigint NULL; cust_id bigint NULL; acct_name varchar(255) NULL; acct_type varchar(64) NULL; acct_login_name varchar(255) NULL; seq_nbr bigint NULL; status_cd varchar(64) NULL; create_date datetime NULL; update_date datetime NULL; region_id bigint NULL; ... 共 28 列

### customer
- table_name: customer
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 890000
- index_count: 3
- has_indexes: yes
- index_names: PRIMARY, idx_customer_cust_id, idx_customer_status_region
- index_columns: PRIMARY(id) | idx_customer_cust_id(cust_id) | idx_customer_status_region(status_cd,region_id)
- column_count: 24
- key_columns_hint: id, cust_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: id bigint NOT NULL; cust_id bigint NULL; cust_name varchar(255) NULL; cust_type varchar(64) NULL; status_cd varchar(64) NULL; region_id bigint NULL; create_date datetime NULL; update_date datetime NULL; ... 共 24 列

### inf_bc_prod_inst
- table_name: inf_bc_prod_inst
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 5200000
- index_count: 4
- has_indexes: yes
- index_names: idx_prod_inst_owner_cust, idx_prod_inst_order_item, idx_prod_inst_status, idx_prod_inst_prod_inst_id
- index_columns: idx_prod_inst_owner_cust(owner_cust_id) | idx_prod_inst_order_item(last_order_item_id) | idx_prod_inst_status(status_cd,update_date) | idx_prod_inst_prod_inst_id(prod_inst_id)
- column_count: 56
- key_columns_hint: prod_inst_id, owner_cust_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: prod_inst_id bigint NULL; owner_cust_id bigint NULL; status_cd varchar(64) NULL; acc_num varchar(64) NULL; user_name varchar(255) NULL; create_date datetime NULL; update_date datetime NULL; last_order_item_id bigint NULL; ... 共 56 列

### inf_bc_order_item
- table_name: inf_bc_order_item
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 12600000
- index_count: 4
- has_indexes: yes
- index_names: idx_order_item_agreement, idx_order_item_cust_order, idx_order_item_sequence, idx_order_item_order_item_id
- index_columns: idx_order_item_agreement(agreement_id) | idx_order_item_cust_order(cust_order_id) | idx_order_item_sequence(item_sequence) | idx_order_item_order_item_id(order_item_id)
- column_count: 42
- key_columns_hint: order_item_id, cust_order_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: order_item_id bigint NULL; agreement_id bigint NULL; cust_order_id bigint NULL; service_id bigint NULL; deal_order varchar(64) NULL; item_sequence bigint NULL; complete_date datetime NULL; crm_finish_date datetime NULL; ... 共 42 列

### inf_bc_prod_inst_acct_rel
- table_name: inf_bc_prod_inst_acct_rel
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 6800000
- index_count: 4
- has_indexes: yes
- index_names: idx_piar_acct_id, idx_piar_prod_inst_id, idx_piar_status, idx_piar_agree_id
- index_columns: idx_piar_acct_id(acct_id) | idx_piar_prod_inst_id(prod_inst_id) | idx_piar_status(status_cd) | idx_piar_agree_id(agree_id)
- column_count: 18
- key_columns_hint: prod_inst_acct_rel_id, acct_id, prod_inst_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: prod_inst_acct_rel_id bigint NULL; acct_id bigint NULL; agree_id bigint NULL; prod_inst_id bigint NULL; status_cd varchar(64) NULL; priority int NULL; create_date datetime NULL; update_date datetime NULL; ... 共 18 列

### inf_bc_offer_inst
- table_name: inf_bc_offer_inst
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 4300000
- index_count: 4
- has_indexes: yes
- index_names: idx_offer_inst_owner_cust, idx_offer_inst_offer_id, idx_offer_inst_status, idx_offer_inst_order_item
- index_columns: idx_offer_inst_owner_cust(owner_cust_id) | idx_offer_inst_offer_id(offer_id) | idx_offer_inst_status(status_cd,create_date) | idx_offer_inst_order_item(last_order_item_id)
- column_count: 37
- key_columns_hint: offer_inst_id, owner_cust_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: offer_inst_id bigint NULL; owner_cust_id bigint NULL; offer_id bigint NULL; status_cd varchar(64) NULL; create_date datetime NULL; update_date datetime NULL; offer_type varchar(64) NULL; region_id bigint NULL; ... 共 37 列

### inf_bc_tran_offer
- table_name: inf_bc_tran_offer
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 980000
- index_count: 3
- has_indexes: yes
- index_names: idx_tran_offer_agreement, idx_tran_offer_order_item, idx_tran_offer_prod_offer_inst
- index_columns: idx_tran_offer_agreement(agreement_id) | idx_tran_offer_order_item(order_item_id) | idx_tran_offer_prod_offer_inst(prod_offer_inst_id)
- column_count: 12
- key_columns_hint: prod_offer_inst_id, agreement_id, order_item_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: agreement_id bigint NULL; order_item_id bigint NULL; offer_id bigint NULL; prod_offer_inst_id bigint NULL; spec_attr varchar(255) NULL; create_date datetime NULL; exp_date datetime NULL; oper_type varchar(16) NULL; ... 共 12 列

### audit_log
- table_name: audit_log
- db_type: mysql
- db_name: CUSDBX
- db_ip: 127.0.0.1
- db_port: 3306
- table_rows_exact: 8600000
- index_count: 4
- has_indexes: yes
- index_names: idx_audit_log_user_id, idx_audit_log_created_at, idx_audit_log_request_path, idx_audit_log_user_time
- index_columns: idx_audit_log_user_id(user_id) | idx_audit_log_created_at(created_at) | idx_audit_log_request_path(request_path) | idx_audit_log_user_time(user_id,created_at)
- column_count: 15
- key_columns_hint: id, user_id
- ddl_available: yes
- db_version: shadow-mysql-8.0
- column_definitions: id bigint NOT NULL; user_id bigint NULL; request_path varchar(255) NULL; request_method varchar(16) NULL; trace_id varchar(64) NULL; result_code varchar(32) NULL; created_at datetime NULL; cost_ms bigint NULL; ... 共 15 列

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
  `acct_name` varchar(255) DEFAULT NULL,
  `acct_type` varchar(64) DEFAULT NULL,
  `acct_login_name` varchar(255) DEFAULT NULL,
  `seq_nbr` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
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
  `cust_name` varchar(255) DEFAULT NULL,
  `cust_type` varchar(64) DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `region_id` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
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
  `acc_num` varchar(64) DEFAULT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
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
  `service_id` bigint DEFAULT NULL,
  `deal_order` varchar(64) DEFAULT NULL,
  `item_sequence` bigint DEFAULT NULL,
  `complete_date` datetime DEFAULT NULL,
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
  `agree_id` bigint DEFAULT NULL,
  `prod_inst_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
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
  `offer_id` bigint DEFAULT NULL,
  `status_cd` varchar(64) DEFAULT NULL,
  `offer_type` varchar(64) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
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
  `spec_attr` varchar(255) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `exp_date` datetime DEFAULT NULL,
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
  `request_method` varchar(16) DEFAULT NULL,
  `trace_id` varchar(64) DEFAULT NULL,
  `result_code` varchar(32) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `cost_ms` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_audit_log_user_id` (`user_id`),
  KEY `idx_audit_log_created_at` (`created_at`),
  KEY `idx_audit_log_request_path` (`request_path`),
  KEY `idx_audit_log_user_time` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
