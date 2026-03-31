from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "docs" / "workflow-upload"
BASELINE_DIR = OUTPUT_ROOT / "baseline"
BATCH_DIR = OUTPUT_ROOT / "batch"
DEFAULT_DB_IP = "127.0.0.1"
DEFAULT_DB_PORT = 3306

TABLES: dict[str, dict] = {
    "account": {
        "table_name": "account",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 150000,
        "primary_key": [],
        "columns": [
            {"name": "acct_id", "data_type": "bigint", "nullable": True},
            {"name": "cust_id", "data_type": "bigint", "nullable": True},
            {"name": "status_cd", "data_type": "varchar(64)", "nullable": True},
            {"name": "update_date", "data_type": "datetime", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_account_acct_id_cust_id", "columns": ["acct_id", "cust_id"], "unique": False},
            {"name": "idx_account_acct_id", "columns": ["acct_id"], "unique": False},
            {"name": "idx_account_seq_nbr", "columns": ["seq_nbr"], "unique": False},
            {"name": "idx_account_cust_id", "columns": ["cust_id"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["acct_id", "cust_id"],
    },
    "customer": {
        "table_name": "customer",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 890000,
        "primary_key": ["id"],
        "columns": [
            {"name": "id", "data_type": "bigint", "nullable": False},
            {"name": "cust_id", "data_type": "bigint", "nullable": True},
            {"name": "status_cd", "data_type": "varchar(64)", "nullable": True},
            {"name": "region_id", "data_type": "bigint", "nullable": True},
        ],
        "indexes": [
            {"name": "PRIMARY", "columns": ["id"], "unique": True},
            {"name": "idx_customer_cust_id", "columns": ["cust_id"], "unique": False},
            {"name": "idx_customer_status_region", "columns": ["status_cd", "region_id"], "unique": False},
        ],
        "ddl": dedent(
            """
            CREATE TABLE `customer` (
              `id` bigint NOT NULL,
              `cust_id` bigint DEFAULT NULL,
              `status_cd` varchar(64) DEFAULT NULL,
              `region_id` bigint DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `idx_customer_cust_id` (`cust_id`),
              KEY `idx_customer_status_region` (`status_cd`,`region_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        ).strip(),
        "forbidden_primary_key_columns": ["cust_id"],
    },
    "inf_bc_prod_inst": {
        "table_name": "inf_bc_prod_inst",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 5200000,
        "primary_key": [],
        "columns": [
            {"name": "prod_inst_id", "data_type": "bigint", "nullable": True},
            {"name": "owner_cust_id", "data_type": "bigint", "nullable": True},
            {"name": "status_cd", "data_type": "varchar(64)", "nullable": True},
            {"name": "update_date", "data_type": "datetime", "nullable": True},
            {"name": "last_order_item_id", "data_type": "bigint", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_prod_inst_owner_cust", "columns": ["owner_cust_id"], "unique": False},
            {"name": "idx_prod_inst_order_item", "columns": ["last_order_item_id"], "unique": False},
            {"name": "idx_prod_inst_status", "columns": ["status_cd", "update_date"], "unique": False},
            {"name": "idx_prod_inst_prod_inst_id", "columns": ["prod_inst_id"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["prod_inst_id", "owner_cust_id"],
    },
    "inf_bc_order_item": {
        "table_name": "inf_bc_order_item",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 12600000,
        "primary_key": [],
        "columns": [
            {"name": "order_item_id", "data_type": "bigint", "nullable": True},
            {"name": "agreement_id", "data_type": "bigint", "nullable": True},
            {"name": "cust_order_id", "data_type": "bigint", "nullable": True},
            {"name": "item_sequence", "data_type": "bigint", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_order_item_agreement", "columns": ["agreement_id"], "unique": False},
            {"name": "idx_order_item_cust_order", "columns": ["cust_order_id"], "unique": False},
            {"name": "idx_order_item_sequence", "columns": ["item_sequence"], "unique": False},
            {"name": "idx_order_item_order_item_id", "columns": ["order_item_id"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["order_item_id", "cust_order_id"],
    },
    "inf_bc_prod_inst_acct_rel": {
        "table_name": "inf_bc_prod_inst_acct_rel",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 6800000,
        "primary_key": [],
        "columns": [
            {"name": "prod_inst_acct_rel_id", "data_type": "bigint", "nullable": True},
            {"name": "acct_id", "data_type": "bigint", "nullable": True},
            {"name": "prod_inst_id", "data_type": "bigint", "nullable": True},
            {"name": "status_cd", "data_type": "varchar(64)", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_piar_acct_id", "columns": ["acct_id"], "unique": False},
            {"name": "idx_piar_prod_inst_id", "columns": ["prod_inst_id"], "unique": False},
            {"name": "idx_piar_status", "columns": ["status_cd"], "unique": False},
            {"name": "idx_piar_agree_id", "columns": ["agree_id"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["prod_inst_acct_rel_id", "acct_id"],
    },
    "inf_bc_offer_inst": {
        "table_name": "inf_bc_offer_inst",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 4300000,
        "primary_key": [],
        "columns": [
            {"name": "offer_inst_id", "data_type": "bigint", "nullable": True},
            {"name": "owner_cust_id", "data_type": "bigint", "nullable": True},
            {"name": "status_cd", "data_type": "varchar(64)", "nullable": True},
            {"name": "create_date", "data_type": "datetime", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_offer_inst_owner_cust", "columns": ["owner_cust_id"], "unique": False},
            {"name": "idx_offer_inst_offer_id", "columns": ["offer_id"], "unique": False},
            {"name": "idx_offer_inst_status", "columns": ["status_cd", "create_date"], "unique": False},
            {"name": "idx_offer_inst_order_item", "columns": ["last_order_item_id"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["offer_inst_id", "owner_cust_id"],
    },
    "inf_bc_tran_offer": {
        "table_name": "inf_bc_tran_offer",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 980000,
        "primary_key": [],
        "columns": [
            {"name": "agreement_id", "data_type": "bigint", "nullable": True},
            {"name": "order_item_id", "data_type": "bigint", "nullable": True},
            {"name": "offer_id", "data_type": "bigint", "nullable": True},
            {"name": "prod_offer_inst_id", "data_type": "bigint", "nullable": True},
        ],
        "indexes": [
            {"name": "idx_tran_offer_agreement", "columns": ["agreement_id"], "unique": False},
            {"name": "idx_tran_offer_order_item", "columns": ["order_item_id"], "unique": False},
            {"name": "idx_tran_offer_prod_offer_inst", "columns": ["prod_offer_inst_id"], "unique": False},
        ],
        "ddl": dedent(
            """
            CREATE TABLE `inf_bc_tran_offer` (
              `agreement_id` bigint DEFAULT NULL,
              `order_item_id` bigint DEFAULT NULL,
              `offer_id` bigint DEFAULT NULL,
              `prod_offer_inst_id` bigint DEFAULT NULL,
              KEY `idx_tran_offer_agreement` (`agreement_id`),
              KEY `idx_tran_offer_order_item` (`order_item_id`),
              KEY `idx_tran_offer_prod_offer_inst` (`prod_offer_inst_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        ).strip(),
        "forbidden_primary_key_columns": ["prod_offer_inst_id", "agreement_id"],
    },
    "audit_log": {
        "table_name": "audit_log",
        "db_type": "mysql",
        "db_name": "CUSDBX",
        "table_rows_exact": 8600000,
        "primary_key": ["id"],
        "columns": [
            {"name": "id", "data_type": "bigint", "nullable": False},
            {"name": "user_id", "data_type": "bigint", "nullable": True},
            {"name": "request_path", "data_type": "varchar(255)", "nullable": True},
            {"name": "created_at", "data_type": "datetime", "nullable": True},
        ],
        "indexes": [
            {"name": "PRIMARY", "columns": ["id"], "unique": True},
            {"name": "idx_audit_log_user_id", "columns": ["user_id"], "unique": False},
            {"name": "idx_audit_log_created_at", "columns": ["created_at"], "unique": False},
            {"name": "idx_audit_log_request_path", "columns": ["request_path"], "unique": False},
            {"name": "idx_audit_log_user_time", "columns": ["user_id", "created_at"], "unique": False},
        ],
        "ddl": dedent(
            """
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
            """
        ).strip(),
        "forbidden_primary_key_columns": ["user_id", "request_path"],
    },
}

SQLS: list[dict] = [
    {
        "sql_id": "sql_1",
        "title": "account 等值查询",
        "sql": "select * from account where acct_id = 1",
        "template_sql": "select * from account where acct_id = ?",
        "tables": ["account"],
        "required_index_names": ["idx_account_acct_id", "idx_account_acct_id_cust_id"],
        "observation": {"cluster_count": 12, "min_query_time_ms": 120.0, "avg_query_time_ms": 560.0, "max_query_time_ms": 2100.0, "latest_timestamp": "2026-03-18 18:00:00"},
    },
    {
        "sql_id": "sql_2",
        "title": "account 过滤排序分页",
        "sql": "select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20",
        "template_sql": "select acct_id, cust_id, status_cd from account where cust_id = ? order by update_date desc limit ?",
        "tables": ["account"],
        "required_index_names": ["idx_account_cust_id", "idx_account_acct_id_cust_id"],
        "observation": {"cluster_count": 37, "min_query_time_ms": 85.0, "avg_query_time_ms": 430.0, "max_query_time_ms": 1860.0, "latest_timestamp": "2026-03-18 18:06:00"},
    },
    {
        "sql_id": "sql_3",
        "title": "customer 高选择性等值查询",
        "sql": "select * from customer where cust_id = 20001",
        "template_sql": "select * from customer where cust_id = ?",
        "tables": ["customer"],
        "required_index_names": ["PRIMARY", "idx_customer_cust_id"],
        "observation": {"cluster_count": 28, "min_query_time_ms": 40.0, "avg_query_time_ms": 170.0, "max_query_time_ms": 620.0, "latest_timestamp": "2026-03-18 18:09:00"},
    },
    {
        "sql_id": "sql_4",
        "title": "prod_inst 过滤排序分页",
        "sql": "select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50",
        "template_sql": "select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = ? order by update_date desc limit ?",
        "tables": ["inf_bc_prod_inst"],
        "required_index_names": ["idx_prod_inst_owner_cust", "idx_prod_inst_status"],
        "observation": {"cluster_count": 73, "min_query_time_ms": 210.0, "avg_query_time_ms": 980.0, "max_query_time_ms": 4210.0, "latest_timestamp": "2026-03-18 18:12:00"},
    },
    {
        "sql_id": "sql_5",
        "title": "order_item 多条件排序",
        "sql": "select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence",
        "template_sql": "select * from inf_bc_order_item where agreement_id = ? and cust_order_id = ? order by item_sequence",
        "tables": ["inf_bc_order_item"],
        "required_index_names": ["idx_order_item_agreement", "idx_order_item_cust_order", "idx_order_item_sequence"],
        "observation": {"cluster_count": 64, "min_query_time_ms": 320.0, "avg_query_time_ms": 1320.0, "max_query_time_ms": 5860.0, "latest_timestamp": "2026-03-18 18:15:00"},
    },
    {
        "sql_id": "sql_6",
        "title": "prod_inst_acct_rel 多条件过滤",
        "sql": "select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'",
        "template_sql": "select * from inf_bc_prod_inst_acct_rel where acct_id = ? and status_cd = ?",
        "tables": ["inf_bc_prod_inst_acct_rel"],
        "required_index_names": ["idx_piar_acct_id", "idx_piar_status"],
        "observation": {"cluster_count": 22, "min_query_time_ms": 70.0, "avg_query_time_ms": 390.0, "max_query_time_ms": 1330.0, "latest_timestamp": "2026-03-18 18:19:00"},
    },
    {
        "sql_id": "sql_7",
        "title": "offer_inst 过滤排序分页",
        "sql": "select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100",
        "template_sql": "select * from inf_bc_offer_inst where owner_cust_id = ? and status_cd = ? order by create_date desc limit ?",
        "tables": ["inf_bc_offer_inst"],
        "required_index_names": ["idx_offer_inst_owner_cust", "idx_offer_inst_status"],
        "observation": {"cluster_count": 55, "min_query_time_ms": 150.0, "avg_query_time_ms": 760.0, "max_query_time_ms": 3180.0, "latest_timestamp": "2026-03-18 18:23:00"},
    },
    {
        "sql_id": "sql_8",
        "title": "tran_offer 去重排序",
        "sql": "select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id",
        "template_sql": "select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = ? and order_item_id = ? order by prod_offer_inst_id",
        "tables": ["inf_bc_tran_offer"],
        "required_index_names": ["idx_tran_offer_agreement", "idx_tran_offer_order_item", "idx_tran_offer_prod_offer_inst"],
        "observation": {"cluster_count": 19, "min_query_time_ms": 95.0, "avg_query_time_ms": 510.0, "max_query_time_ms": 1490.0, "latest_timestamp": "2026-03-18 18:27:00"},
    },
    {
        "sql_id": "sql_9",
        "title": "audit_log 用户维度查询",
        "sql": "select * from audit_log where user_id = 10001 order by created_at desc limit 100",
        "template_sql": "select * from audit_log where user_id = ? order by created_at desc limit ?",
        "tables": ["audit_log"],
        "required_index_names": ["PRIMARY", "idx_audit_log_user_id", "idx_audit_log_user_time", "idx_audit_log_created_at"],
        "observation": {"cluster_count": 86, "min_query_time_ms": 260.0, "avg_query_time_ms": 1410.0, "max_query_time_ms": 6230.0, "latest_timestamp": "2026-03-18 18:31:00"},
    },
    {
        "sql_id": "sql_10",
        "title": "audit_log 范围聚合",
        "sql": "select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'",
        "template_sql": "select count(*) as total_count from audit_log where created_at >= ? and created_at < ? and request_path like ?",
        "tables": ["audit_log"],
        "required_index_names": ["PRIMARY", "idx_audit_log_created_at", "idx_audit_log_request_path"],
        "observation": {"cluster_count": 14, "min_query_time_ms": 410.0, "avg_query_time_ms": 1860.0, "max_query_time_ms": 7120.0, "latest_timestamp": "2026-03-18 18:35:00"},
    },
]

BASELINE_CASES: list[tuple[str, str, list[str]]] = [
    ("case-a", "Case A - 高选择性等值查询", ["sql_3"]),
    ("case-b", "Case B - 多条件过滤加排序分页", ["sql_2"]),
    ("case-c", "Case C - 范围过滤加聚合统计", ["sql_10"]),
]

V3_BATCH_GROUPS: list[tuple[str, str, list[str]]] = [
    ("group-1", "V3 Group 1 - account 与 customer", ["sql_1", "sql_2", "sql_3"]),
    ("group-2", "V3 Group 2 - 产品与优惠实例", ["sql_4", "sql_6", "sql_7"]),
    ("group-3", "V3 Group 3 - 订单项与交易优惠", ["sql_5", "sql_8"]),
    ("group-4", "V3 Group 4 - 审计日志", ["sql_9", "sql_10"]),
]
GLOBAL_FORBIDDEN_PHRASES = [
    "无索引",
    "索引未知",
    "未显示索引信息",
    "无法确认是否有索引",
    "DDL 未提供",
    "未提供 DDL",
    "DDL 为空",
]


def sql_by_id(sql_id: str) -> dict:
    return next(item for item in SQLS if item["sql_id"] == sql_id)


def version_constraints(version: str) -> list[str]:
    base = [
        "只允许依据 AUTHORIZED_METADATA_JSON 和 LOCAL_FACT_PACKET_JSON 判断表结构、主键、索引、表行数和 DDL。",
        "若 indexes 非空，禁止输出“无索引”“索引未知”“未显示索引信息”或同义表达。",
        "若 table_rows_exact 为数值，禁止改写为 0、未知、空值或忽略不提。",
        "若 ddl 已提供，禁止输出“DDL 未提供”“DDL 为空”或同义表达。",
        "若 primary_key 非空，禁止把其他字段写成主键；若 primary_key 为空，禁止自行猜测主键。",
        "每条 SQL 必须先回显输入事实，再给出性能判断。",
    ]
    if version in {"v2", "v3"}:
        base.extend(
            [
                "若输入事实与经验推断冲突，优先以输入事实为准，并明确写出“输入事实如此提供”。",
                "若认为现有索引不匹配当前 SQL，只能写“现有索引不匹配”，不得否认索引存在。",
            ]
        )
    return base


def compact_table_metadata(table_names: list[str]) -> list[dict]:
    result = []
    for name in table_names:
        table = TABLES[name]
        result.append(
            {
                "table_name": table["table_name"],
                "db_type": table["db_type"],
                "db_name": table["db_name"],
                "table_rows_exact": table["table_rows_exact"],
                "primary_key": table["primary_key"],
                "columns": table["columns"],
                "indexes": table["indexes"],
                "ddl": table["ddl"],
            }
        )
    return result


def local_fact_packet(sql_item: dict) -> dict:
    packet_tables = []
    for table_name in sql_item["tables"]:
        table = TABLES[table_name]
        packet_tables.append(
            {
                "table_name": table_name,
                "table_rows_exact": table["table_rows_exact"],
                "table_rows": table["table_rows_exact"],
                "primary_key": table["primary_key"],
                "primary_key_only": table["primary_key"],
                "indexes": table["indexes"],
                "columns": table["columns"],
                "forbidden_primary_key_columns": table["forbidden_primary_key_columns"],
            }
        )
    return {
        "sql_id": sql_item["sql_id"],
        "required_index_names": sql_item["required_index_names"],
        "tables": packet_tables,
    }


def json_block(data: object) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"


def sql_block(sql: str) -> str:
    return "```sql\n" + sql + "\n```"


def ddl_appendix(table_names: list[str]) -> str:
    sections = ["## 原始 DDL 附录"]
    for table_name in table_names:
        sections.append(f"### {table_name}")
        sections.append(sql_block(TABLES[table_name]["ddl"]))
    return "\n\n".join(sections)


def local_constraints_for_table(table: dict) -> list[str]:
    rules = [
        f"table_rows_exact 与 table_rows 都必须按 {table['table_rows_exact']} 引用，不得改写。",
    ]
    if table["primary_key"]:
        pk_text = ", ".join(table["primary_key"])
        rules.append(f"本表主键仅为 [{pk_text}]，不得将其他字段视为主键。")
    else:
        forbidden = ", ".join(table["forbidden_primary_key_columns"])
        rules.append(f"本表未提供主键信息，禁止把 [{forbidden}] 等字段写成主键。")
    if table["indexes"]:
        index_names = ", ".join(index["name"] for index in table["indexes"])
        rules.append(f"索引已提供：{index_names}。不得写成无索引或索引未知。")
    return rules


def render_sql_unit(sql_item: dict, version: str) -> str:
    table_names = sql_item["tables"]
    lines = [
        f"### {sql_item['sql_id']} - {sql_item['title']}",
        f"- 原始 SQL：`{sql_item['sql']}`",
        f"- 涉及表：{', '.join(table_names)}",
        f"- 本 SQL 必须至少引用这些索引名：{', '.join(sql_item['required_index_names'])}",
        "",
        "#### LOCAL_FACT_PACKET_JSON",
        json_block(local_fact_packet(sql_item)),
        "",
        "#### SQL 文本",
        sql_block(sql_item["sql"]),
        "",
        "#### 观测统计",
        json_block(sql_item["observation"]),
    ]

    for table_name in table_names:
        table = TABLES[table_name]
        lines.extend(
            [
                "",
                f"#### 表 {table_name} 的局部权威事实",
                f"- table_rows_exact: {table['table_rows_exact']}",
                f"- table_rows: {table['table_rows_exact']}",
                f"- primary_key: {table['primary_key'] or []}",
                f"- primary_key_only: {', '.join(table['primary_key']) if table['primary_key'] else 'NONE'}",
                f"- not_primary_key_columns: {', '.join(table['forbidden_primary_key_columns'])}",
                f"- indexes: {', '.join(index['name'] for index in table['indexes'])}",
                f"- columns: {', '.join(column['name'] for column in table['columns'])}",
            ]
        )
        if version in {"v2", "v3"}:
            lines.extend(
                [
                    "",
                    f"#### 表 {table_name} 的事实回显模板",
                    f"- required_output_fact_line: table_name={table_name}; table_rows={table['table_rows_exact']}; primary_key_only={','.join(table['primary_key']) if table['primary_key'] else 'NONE'}; required_index_names={','.join(index['name'] for index in table['indexes'])}",
                    "",
                    f"#### 表 {table_name} 的 DDL 摘要",
                    sql_block(table["ddl"]),
                    "",
                    f"#### 表 {table_name} 的本节分析约束",
                ]
            )
            lines.extend([f"- {rule}" for rule in local_constraints_for_table(table)])
        if version == "v3":
            pk_text = ", ".join(table["primary_key"]) if table["primary_key"] else "NONE"
            non_pk_text = ", ".join(table["forbidden_primary_key_columns"])
            index_text = ", ".join(index["name"] for index in table["indexes"])
            lines.extend(
                [
                    "",
                    f"#### 表 {table_name} 的强制事实声明",
                    f"- {table_name} 的 table_rows 和 table_rows_exact 都是 {table['table_rows_exact']}，不是 0。",
                    f"- {table_name} 的主键只有 {pk_text}。",
                    f"- {table_name} 的非主键字段包括 {non_pk_text}。",
                    f"- {table_name} 已提供索引：{index_text}。",
                ]
            )

    return "\n".join(lines)


def render_connection_info() -> str:
    return "\n".join(
        [
            "## 数据库连接信息",
            f"- mysql://{DEFAULT_DB_IP}:{DEFAULT_DB_PORT}/CUSDBX",
        ]
    )


def render_metadata_summary(table_names: list[str]) -> str:
    lines = ["## 权威表元数据摘要"]
    for table_name in table_names:
        table = TABLES[table_name]
        lines.extend(
            [
                f"### {table_name}",
                f"- table_name: {table_name}",
                f"- db_type: {table['db_type']}",
                f"- db_name: {table['db_name']}",
                f"- db_ip: {DEFAULT_DB_IP}",
                f"- db_port: {DEFAULT_DB_PORT}",
                f"- table_rows_exact: {table['table_rows_exact']}",
                f"- table_rows: {table['table_rows_exact']}",
                f"- primary_key: {table['primary_key'] or []}",
                f"- primary_key_only: {', '.join(table['primary_key']) if table['primary_key'] else 'NONE'}",
                f"- not_primary_key_columns: {', '.join(table['forbidden_primary_key_columns'])}",
                f"- index_count: {len(table['indexes'])}",
                f"- has_indexes: {'yes' if table['indexes'] else 'no'}",
                f"- index_names: {', '.join(index['name'] for index in table['indexes'])}",
                f"- ddl_available: yes",
            ]
        )
    return "\n".join(lines)


def render_sql_list(sql_items: list[dict]) -> str:
    lines = ["## SQL 列表"]
    for position, sql_item in enumerate(sql_items, start=1):
        lines.extend(
            [
                f"### SQL {position}",
                f"- sql_id: {sql_item['sql_id']}",
                "- db_type: mysql",
                "- db_name: CUSDBX",
                f"- db_ip: {DEFAULT_DB_IP}",
                f"- db_port: {DEFAULT_DB_PORT}",
                f"- template_sql: {sql_item['template_sql']}",
                f"- table_names: {', '.join(sql_item['tables'])}",
                sql_block(sql_item["sql"]),
            ]
        )
    return "\n".join(lines)


def render_sql_observations(sql_items: list[dict]) -> str:
    lines = ["## SQL 观测统计"]
    for position, sql_item in enumerate(sql_items, start=1):
        obs = sql_item["observation"]
        lines.extend(
            [
                f"### 观测项 {position}",
                "- db_type: mysql",
                "- db_name: CUSDBX",
                f"- db_ip: {DEFAULT_DB_IP}",
                f"- cluster_count: {obs['cluster_count']}",
                f"- min_query_time_ms: {obs['min_query_time_ms']}",
                f"- avg_query_time_ms: {obs['avg_query_time_ms']}",
                f"- max_query_time_ms: {obs['max_query_time_ms']}",
                f"- latest_timestamp: {obs['latest_timestamp']}",
                sql_block(sql_item["sql"]),
            ]
        )
    return "\n".join(lines)


def render_document(title: str, sql_ids: list[str], version: str, *, focused_upload: bool) -> tuple[str, dict]:
    sql_items = [sql_by_id(sql_id) for sql_id in sql_ids]
    table_names: list[str] = []
    for sql_item in sql_items:
        for table_name in sql_item["tables"]:
            if table_name not in table_names:
                table_names.append(table_name)

    intro = [
        "# 慢 SQL 分析输入文档",
        "",
        f"- 版本：{version.upper()}",
        f"- 上传策略：{'短文聚焦上传' if focused_upload else '集中上传'}",
        f"- SQL 数量：{len(sql_items)}",
        "",
        "## 分析规则",
    ]
    intro.extend([f"- {rule}" for rule in version_constraints(version)])
    intro.extend(
        [
            "",
            render_connection_info(),
            "",
            "## AUTHORIZED_METADATA_JSON",
            json_block({"tables": compact_table_metadata(table_names)}),
            "",
            render_metadata_summary(table_names),
            "",
            render_sql_list(sql_items),
            "",
            "## SQL 局部权威事实包",
        ]
    )
    for sql_item in sql_items:
        intro.append(render_sql_unit(sql_item, version))
    intro.extend(
        [
            "",
            render_sql_observations(sql_items),
            "",
            ddl_appendix(table_names),
            "",
            "## 元数据缺失说明",
            "- 本次分析所涉及的表元数据已完整命中",
        ]
    )

    manifest = {
        "title": title,
        "version": version,
        "focused_upload": focused_upload,
        "sql_ids": sql_ids,
        "sql_units": [
            {
                "sql_id": item["sql_id"],
                "title": item["title"],
                "tables": item["tables"],
                "required_index_names": item["required_index_names"],
                "table_expectations": [
                    {
                        "table_name": table_name,
                        "table_rows_exact": TABLES[table_name]["table_rows_exact"],
                        "primary_key": TABLES[table_name]["primary_key"],
                        "forbidden_primary_key_columns": TABLES[table_name]["forbidden_primary_key_columns"],
                    }
                    for table_name in item["tables"]
                ],
            }
            for item in sql_items
        ],
        "global_forbidden_phrases": GLOBAL_FORBIDDEN_PHRASES,
    }
    return "\n".join(intro).strip() + "\n", manifest


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_artifacts() -> list[Path]:
    written: list[Path] = []

    for case_id, title, sql_ids in BASELINE_CASES:
        for version in ("v1", "v2", "v3"):
            content, manifest = render_document(title, sql_ids, version, focused_upload=(version == "v3"))
            md_path = BASELINE_DIR / f"{case_id}.{version}.md"
            manifest_path = BASELINE_DIR / f"{case_id}.{version}.manifest.json"
            write_text(md_path, content)
            write_json(manifest_path, manifest)
            written.extend([md_path, manifest_path])

    for version in ("v1", "v2"):
        content, manifest = render_document(
            f"Batch All 10 - {version.upper()}",
            [item["sql_id"] for item in SQLS],
            version,
            focused_upload=False,
        )
        md_path = BATCH_DIR / f"all-10.{version}.md"
        manifest_path = BATCH_DIR / f"all-10.{version}.manifest.json"
        write_text(md_path, content)
        write_json(manifest_path, manifest)
        written.extend([md_path, manifest_path])

    for group_id, title, sql_ids in V3_BATCH_GROUPS:
        content, manifest = render_document(title, sql_ids, "v3", focused_upload=True)
        md_path = BATCH_DIR / f"{group_id}.v3.md"
        manifest_path = BATCH_DIR / f"{group_id}.v3.manifest.json"
        write_text(md_path, content)
        write_json(manifest_path, manifest)
        written.extend([md_path, manifest_path])

    checklist = dedent(
        """
        # 工作流验收清单

        1. 先跑 baseline 的 `case-a -> case-b -> case-c`，每个版本都只在前一版失败时才升级到下一版。
        2. 报告必须能回显：表名、table_rows_exact、主键、至少一个已提供索引名。
        3. 报告不得出现：`无索引`、`索引未知`、`未显示索引信息`、`DDL 未提供`、`未提供 DDL`。
        4. 若表主键为空，报告不得凭经验把业务字段写成主键。
        5. baseline 通过后，再跑 `batch/all-10.v2.md`；若批量退化，再改跑 `batch/group-*.v3.md`。
        6. 若 `v1 -> v2 -> v3` 仍无法稳定通过，结论应记录为“仅靠上传文件格式无法彻底修复，需要工作流侧调整提示词或校验”。
        """
    ).strip() + "\n"
    checklist_path = OUTPUT_ROOT / "checklist.md"
    write_text(checklist_path, checklist)
    written.append(checklist_path)
    return written


if __name__ == "__main__":
    paths = build_artifacts()
    print(f"generated={len(paths)}")
    for path in paths:
        print(path)
