import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pymysql


LINE_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<payload>\{.*\})$")
LEADING_COMMENT_RE = re.compile(r"^/\*.*?\*/\s*", re.DOTALL)
SQL_START_RE = re.compile(r"^(SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
FROM_CLAUSE_RE = re.compile(
    r"\bFROM\b\s+(.+?)(?:\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|\bFOR\b|\bUNION\b|$)",
    re.IGNORECASE | re.DOTALL,
)
JOIN_RE = re.compile(r"\bJOIN\b\s+([`\"]?\w+[`\"]?)(?:\s+(?:AS\s+)?([`\"]?\w+[`\"]?))?", re.IGNORECASE)
UPDATE_RE = re.compile(r"\bUPDATE\b\s+([`\"]?\w+[`\"]?)(?:\s+(?:AS\s+)?([`\"]?\w+[`\"]?))?", re.IGNORECASE)
INSERT_RE = re.compile(r"\bINSERT\b\s+INTO\b\s+([`\"]?\w+[`\"]?)", re.IGNORECASE)
DELETE_RE = re.compile(r"\bDELETE\b\s+FROM\b\s+([`\"]?\w+[`\"]?)", re.IGNORECASE)
SELECT_RE = re.compile(r"\bSELECT\b\s+(.+?)\bFROM\b", re.IGNORECASE | re.DOTALL)
WHERE_RE = re.compile(
    r"\bWHERE\b\s+(.+?)(?:\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|\bFOR\b|$)",
    re.IGNORECASE | re.DOTALL,
)
ORDER_BY_RE = re.compile(r"\bORDER\s+BY\b\s+(.+?)(?:\bLIMIT\b|\bFOR\b|$)", re.IGNORECASE | re.DOTALL)
GROUP_BY_RE = re.compile(r"\bGROUP\s+BY\b\s+(.+?)(?:\bORDER\s+BY\b|\bLIMIT\b|$)", re.IGNORECASE | re.DOTALL)
UPDATE_SET_RE = re.compile(r"\bSET\b\s+(.+?)(?:\bWHERE\b|$)", re.IGNORECASE | re.DOTALL)
INSERT_COLUMNS_RE = re.compile(
    r"\bINSERT\b\s+INTO\b\s+[`\"]?\w+[`\"]?\s*\((.*?)\)\s*VALUES",
    re.IGNORECASE | re.DOTALL,
)
QUALIFIED_COLUMN_RE = re.compile(r"([`\"]?\w+[`\"]?)\.([`\"]?\w+[`\"]?)")
JOIN_COMPARISON_RE = re.compile(
    r"([`\"]?\w+[`\"]?)\.([`\"]?\w+[`\"]?)\s*=\s*([`\"]?\w+[`\"]?)\.([`\"]?\w+[`\"]?)",
    re.IGNORECASE,
)
COMPARISON_RE = re.compile(
    r"([`\"]?\w+[`\"]?)\s*(=|<>|!=|>=|<=|>|<|LIKE)\s*('(?:''|[^'])*'|\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
IN_RE = re.compile(r"([`\"]?\w+[`\"]?)\s+IN\s*\(", re.IGNORECASE)
IS_NULL_RE = re.compile(r"([`\"]?\w+[`\"]?)\s+IS\s+(?:NOT\s+)?NULL", re.IGNORECASE)
AS_RE = re.compile(r"\s+AS\s+", re.IGNORECASE)
SQL_KEYWORDS = {
    "select",
    "from",
    "where",
    "and",
    "or",
    "on",
    "left",
    "right",
    "inner",
    "outer",
    "join",
    "limit",
    "group",
    "order",
    "by",
    "asc",
    "desc",
    "case",
    "when",
    "then",
    "else",
    "end",
    "distinct",
    "null",
    "is",
    "not",
    "in",
    "like",
}
TYPE_PRIORITY = {
    "VARCHAR(255)": 1,
    "VARCHAR(64)": 2,
    "TINYINT": 3,
    "BIGINT": 4,
    "DATETIME": 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local MySQL shadow schema from UDAL audit logs")
    parser.add_argument("logfiles", nargs="+", type=Path, help="UDAL audit log paths")
    parser.add_argument("--schema", default="CUSDBX", help="Schema name to extract from logs")
    parser.add_argument("--shadow-host", default="127.0.0.1")
    parser.add_argument("--shadow-port", type=int, default=3307)
    parser.add_argument("--shadow-user", default="slow_sql")
    parser.add_argument("--shadow-password", default="slow_sql")
    parser.add_argument("--shadow-db", default="CUSDBX", help="Local shadow schema name")
    parser.add_argument("--cache-db", default="slow_sql_db", help="Metadata cache database name")
    parser.add_argument("--cache-target-host", default="127.0.0.1", help="Original host shown in slow SQL records")
    parser.add_argument("--cache-target-port", type=int, default=3306, help="Original port shown in slow SQL records")
    parser.add_argument("--reset-shadow", action="store_true", help="Drop and recreate the local shadow schema")
    parser.add_argument("--skip-cache-sync", action="store_true", help="Only create the shadow schema")
    return parser.parse_args()


def clean_sql(sql: str) -> str | None:
    sql = LEADING_COMMENT_RE.sub("", sql or "").strip()
    sql = re.sub(r"\s+", " ", sql)
    if not sql:
        return None
    if sql.lower() in {"commit", "begin", "rollback"}:
        return None
    if sql.lower().startswith("set "):
        return None
    if sql.lower().startswith("udal "):
        return None
    if not SQL_START_RE.match(sql):
        return None
    return sql


def normalize_identifier(token: str) -> str:
    cleaned = (token or "").strip().strip(",;")
    cleaned = cleaned.replace("`", "").replace('"', "")
    cleaned = cleaned.split()[0]
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned.lower()


def split_csv(fragment: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in fragment:
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        if char == "," and depth == 0:
            value = "".join(current).strip()
            if value:
                items.append(value)
            current = []
            continue
        current.append(char)
    value = "".join(current).strip()
    if value:
        items.append(value)
    return items


def parse_table_reference(fragment: str) -> tuple[str, str] | None:
    text = fragment.strip()
    if not text or text.startswith("("):
        return None
    text = re.split(r"\bUSE\s+INDEX\b|\bFORCE\s+INDEX\b|\bIGNORE\s+INDEX\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    tokens = text.split()
    if not tokens:
        return None
    table_name = normalize_identifier(tokens[0])
    if not table_name:
        return None
    alias = table_name
    if len(tokens) >= 3 and tokens[1].upper() == "AS":
        alias = normalize_identifier(tokens[2]) or alias
    elif len(tokens) >= 2 and tokens[1].upper() not in SQL_KEYWORDS:
        alias = normalize_identifier(tokens[1]) or alias
    return table_name, alias


def extract_tables_and_aliases(sql: str) -> tuple[list[str], dict[str, str]]:
    tables: list[str] = []
    alias_map: dict[str, str] = {}

    from_match = FROM_CLAUSE_RE.search(sql)
    if from_match:
        for segment in split_csv(from_match.group(1)):
            parsed = parse_table_reference(segment)
            if not parsed:
                continue
            table_name, alias = parsed
            if table_name not in tables:
                tables.append(table_name)
            alias_map[alias] = table_name
            alias_map[table_name] = table_name

    for table_token, alias_token in JOIN_RE.findall(sql):
        table_name = normalize_identifier(table_token)
        alias = normalize_identifier(alias_token) or table_name
        if table_name and table_name not in tables:
            tables.append(table_name)
        if table_name:
            alias_map[alias] = table_name
            alias_map[table_name] = table_name

    update_match = UPDATE_RE.search(sql)
    if update_match:
        table_name = normalize_identifier(update_match.group(1))
        alias = normalize_identifier(update_match.group(2)) or table_name
        if table_name and table_name not in tables:
            tables.append(table_name)
        if table_name:
            alias_map[alias] = table_name
            alias_map[table_name] = table_name

    insert_match = INSERT_RE.search(sql)
    if insert_match:
        table_name = normalize_identifier(insert_match.group(1))
        if table_name and table_name not in tables:
            tables.append(table_name)
            alias_map[table_name] = table_name

    delete_match = DELETE_RE.search(sql)
    if delete_match:
        table_name = normalize_identifier(delete_match.group(1))
        if table_name and table_name not in tables:
            tables.append(table_name)
            alias_map[table_name] = table_name

    return tables, alias_map


def guess_column_type(column_name: str, literal: str | None = None) -> str:
    name = column_name.lower()
    stripped_literal = (literal or "").strip("'")
    if name == "id" or name.endswith("_id") or name.endswith("_seq") or name.endswith("_nbr"):
        return "BIGINT"
    if name.endswith("_staff") or name.endswith("_name") or name.endswith("_addr") or name.endswith("_org") or name.endswith("_phone"):
        return "VARCHAR(255)"
    if "date" in name or "time" in name:
        return "DATETIME"
    if name.startswith("is_") or name.endswith("_flag") or name == "flag":
        return "TINYINT"
    if name.endswith("_count") or name in {"count", "seq_nbr", "deal_order"}:
        return "BIGINT"
    if any(token in name for token in ("_reason", "_remark", "_desc")):
        return "VARCHAR(255)"
    if any(token in name for token in ("_code", "_type", "_state", "_status", "_cd", "_num")):
        return "VARCHAR(64)"
    if stripped_literal and re.fullmatch(r"\d+", stripped_literal) and not (literal or "").startswith("'"):
        return "BIGINT"
    return "VARCHAR(255)"


def merge_column_type(existing_type: str | None, new_type: str) -> str:
    if not existing_type:
        return new_type
    if TYPE_PRIORITY.get(new_type, 0) >= TYPE_PRIORITY.get(existing_type, 0):
        return new_type
    return existing_type


def extract_identifier_list(fragment: str) -> list[str]:
    identifiers: list[str] = []
    for segment in split_csv(fragment):
        text = re.sub(r"\bASC\b|\bDESC\b", "", segment, flags=re.IGNORECASE).strip()
        text = AS_RE.split(text)[0].strip()
        if not text or text == "*":
            continue
        if "(" in text and ")" in text:
            continue
        if re.fullmatch(r"[`\"]?\w+(?:\.[`\"]?\w+)?[`\"]?", text):
            identifier = normalize_identifier(text)
            if identifier and not identifier.isdigit() and identifier.lower() not in SQL_KEYWORDS:
                identifiers.append(identifier)
    return identifiers


def build_shadow_models(sql_statements: list[str]) -> tuple[dict[str, dict], Counter]:
    tables: dict[str, dict] = {}
    table_usage = Counter()

    def ensure_table(table_name: str) -> dict:
        model = tables.setdefault(
            table_name,
            {
                "columns": {},
                "index_counter": Counter(),
            },
        )
        return model

    def add_column(table_name: str, column_name: str, literal: str | None = None) -> None:
        if not table_name or not column_name or column_name == "*" or column_name.isdigit():
            return
        model = ensure_table(table_name)
        guessed_type = guess_column_type(column_name, literal)
        current_type = model["columns"].get(column_name)
        model["columns"][column_name] = merge_column_type(current_type, guessed_type)

    def add_index(table_name: str, columns: list[str]) -> None:
        normalized_list: list[str] = []
        seen_columns: set[str] = set()
        for column in columns:
            if not column or column == "*" or column in seen_columns:
                continue
            seen_columns.add(column)
            normalized_list.append(column)
        normalized = tuple(normalized_list)
        if not table_name or not normalized:
            return
        ensure_table(table_name)["index_counter"][normalized] += 1

    for sql in sql_statements:
        table_names, alias_map = extract_tables_and_aliases(sql)
        single_table = table_names[0] if len(table_names) == 1 else None

        for table_name in table_names:
            ensure_table(table_name)
            table_usage[table_name] += 1

        for alias_token, column_token in QUALIFIED_COLUMN_RE.findall(sql):
            alias = normalize_identifier(alias_token)
            column_name = normalize_identifier(column_token)
            table_name = alias_map.get(alias)
            if table_name:
                add_column(table_name, column_name)

        for left_alias, left_column, right_alias, right_column in JOIN_COMPARISON_RE.findall(sql):
            left_table = alias_map.get(normalize_identifier(left_alias))
            right_table = alias_map.get(normalize_identifier(right_alias))
            left_name = normalize_identifier(left_column)
            right_name = normalize_identifier(right_column)
            if left_table:
                add_column(left_table, left_name)
                add_index(left_table, [left_name])
            if right_table:
                add_column(right_table, right_name)
                add_index(right_table, [right_name])

        where_match = WHERE_RE.search(sql)
        if single_table and where_match:
            where_fragment = where_match.group(1)
            filter_columns: list[str] = []
            for column_token, _operator, literal in COMPARISON_RE.findall(where_fragment):
                column_name = normalize_identifier(column_token)
                add_column(single_table, column_name, literal)
                filter_columns.append(column_name)
            for column_token in IN_RE.findall(where_fragment):
                column_name = normalize_identifier(column_token)
                add_column(single_table, column_name)
                filter_columns.append(column_name)
            for column_token in IS_NULL_RE.findall(where_fragment):
                column_name = normalize_identifier(column_token)
                add_column(single_table, column_name)
                filter_columns.append(column_name)
            if filter_columns:
                add_index(single_table, filter_columns[:2])

        if single_table:
            order_match = ORDER_BY_RE.search(sql)
            if order_match:
                order_columns = extract_identifier_list(order_match.group(1))
                for column_name in order_columns:
                    add_column(single_table, column_name)
                if order_columns:
                    add_index(single_table, order_columns[:2])

            group_match = GROUP_BY_RE.search(sql)
            if group_match:
                group_columns = extract_identifier_list(group_match.group(1))
                for column_name in group_columns:
                    add_column(single_table, column_name)
                if group_columns:
                    add_index(single_table, group_columns[:2])

            select_match = SELECT_RE.search(sql)
            if select_match:
                for column_name in extract_identifier_list(select_match.group(1)):
                    add_column(single_table, column_name)

            update_match = UPDATE_SET_RE.search(sql)
            if update_match:
                for assignment in split_csv(update_match.group(1)):
                    column_name = normalize_identifier(assignment.split("=", 1)[0])
                    add_column(single_table, column_name)

            insert_match = INSERT_COLUMNS_RE.search(sql)
            if insert_match:
                for column_name in extract_identifier_list(insert_match.group(1)):
                    add_column(single_table, column_name)

    return tables, table_usage


def choose_primary_key(table_name: str, columns: dict[str, str]) -> str | None:
    candidates = [
        "id",
        f"{table_name}_id",
        f"{table_name.rstrip('s')}_id",
    ]
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def estimate_rows(usage_count: int) -> int:
    if usage_count >= 5000:
        return 300000
    if usage_count >= 1000:
        return 150000
    if usage_count >= 200:
        return 80000
    if usage_count >= 50:
        return 30000
    return 10000


def build_create_table_sql(table_name: str, model: dict) -> str:
    columns = model["columns"]
    if not columns:
        columns = {"shadow_id": "BIGINT"}
    primary_key = choose_primary_key(table_name, columns)
    ordered_columns = []
    if primary_key:
        ordered_columns.append(primary_key)
    ordered_columns.extend(column for column in sorted(columns) if column != primary_key)

    lines = [
        (
            f"  `{column_name}` {columns[column_name]} NOT NULL"
            if column_name == primary_key
            else f"  `{column_name}` {columns[column_name]} NULL"
        )
        for column_name in ordered_columns
    ]
    if primary_key:
        lines.append(f"  PRIMARY KEY (`{primary_key}`)")

    used_indexes = set()
    for index_columns, _count in model["index_counter"].most_common():
        normalized = tuple(column for column in index_columns if column in columns and column != primary_key)
        if not normalized or normalized in used_indexes:
            continue
        used_indexes.add(normalized)
        index_name = f"idx_{table_name}_{'_'.join(normalized)}"
        if len(index_name) > 60:
            index_name = index_name[:60]
        joined_columns = ", ".join(f"`{column}`" for column in normalized)
        lines.append(f"  KEY `{index_name}` ({joined_columns})")
        if len(used_indexes) >= 4:
            break

    joined_lines = ",\n".join(lines)
    return (
        f"CREATE TABLE `{table_name}` (\n"
        f"{joined_lines}\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    )


def load_sql_statements(logfiles: list[Path], schema_name: str) -> list[str]:
    sql_statements: list[str] = []
    for log_path in logfiles:
        if not log_path.exists():
            raise FileNotFoundError(f"log file not found: {log_path}")
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n")
                match = LINE_RE.match(line)
                if not match:
                    continue
                payload = json.loads(match.group("payload"))
                if payload.get("eventType") != "RECEIVE_REQUEST":
                    continue
                if (payload.get("schema") or "").upper() != schema_name.upper():
                    continue
                sql = clean_sql(payload.get("sql", ""))
                if sql:
                    sql_statements.append(sql)
    return sql_statements


def sync_shadow_schema(
    connection,
    shadow_db: str,
    table_models: dict[str, dict],
    table_usage: Counter,
    reset_shadow: bool,
) -> dict[str, int]:
    with connection.cursor() as cursor:
        if reset_shadow:
            cursor.execute(f"DROP DATABASE IF EXISTS `{shadow_db}`")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{shadow_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        cursor.execute(f"USE `{shadow_db}`")

        if reset_shadow:
            for table_name in table_models:
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS `__shadow_table_stats` ("
            "  `table_name` varchar(128) NOT NULL,"
            "  `estimated_rows` bigint NOT NULL,"
            "  PRIMARY KEY (`table_name`)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        )

        estimated_rows_by_table: dict[str, int] = {}
        for table_name, model in sorted(table_models.items()):
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            cursor.execute(build_create_table_sql(table_name, model))
            estimated_rows = estimate_rows(table_usage[table_name])
            estimated_rows_by_table[table_name] = estimated_rows
            cursor.execute(
                "REPLACE INTO `__shadow_table_stats` (`table_name`, `estimated_rows`) VALUES (%s, %s)",
                (table_name, estimated_rows),
            )
        connection.commit()
        return estimated_rows_by_table


def sync_metadata_cache(
    connection,
    logical_db_name: str,
    shadow_db: str,
    cache_db: str,
    cache_target_host: str,
    cache_target_port: int,
    estimated_rows_by_table: dict[str, int],
) -> int:
    inserted_rows = 0
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM `{cache_db}`.`database_info` "
            "WHERE db_type = %s AND db_name = %s AND db_ip = %s AND db_port = %s",
            ("mysql", logical_db_name, cache_target_host, cache_target_port),
        )

        for table_name, estimated_rows in sorted(estimated_rows_by_table.items()):
            cursor.execute(f"USE `{shadow_db}`")
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_row = cursor.fetchone()
            ddl = create_row[1] if create_row and len(create_row) > 1 else ""
            cursor.execute(
                f"INSERT INTO `{cache_db}`.`database_info` "
                "("
                "db_type, db_name, db_desc, db_ip, db_port, db_version, "
                "table_name, table_desc, table_rows, ddl"
                ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    "mysql",
                    logical_db_name,
                    "CUSDBX local shadow metadata",
                    cache_target_host,
                    cache_target_port,
                    "shadow-mysql-8.0",
                    table_name,
                    "inferred from UDAL audit logs",
                    estimated_rows,
                    ddl,
                ),
            )
            inserted_rows += 1
        connection.commit()
    return inserted_rows


def main() -> int:
    args = parse_args()
    sql_statements = load_sql_statements(args.logfiles, args.schema)
    if not sql_statements:
        print(f"No eligible SQL found for schema {args.schema}.")
        return 0

    table_models, table_usage = build_shadow_models(sql_statements)
    connection = pymysql.connect(
        host=args.shadow_host,
        port=args.shadow_port,
        user=args.shadow_user,
        password=args.shadow_password,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        estimated_rows_by_table = sync_shadow_schema(
            connection=connection,
            shadow_db=args.shadow_db,
            table_models=table_models,
            table_usage=table_usage,
            reset_shadow=args.reset_shadow,
        )
        inserted_rows = 0
        if not args.skip_cache_sync:
            inserted_rows = sync_metadata_cache(
                connection=connection,
                logical_db_name=args.schema,
                shadow_db=args.shadow_db,
                cache_db=args.cache_db,
                cache_target_host=args.cache_target_host,
                cache_target_port=args.cache_target_port,
                estimated_rows_by_table=estimated_rows_by_table,
            )
    finally:
        connection.close()

    print(
        f"Built shadow schema {args.shadow_db} with {len(table_models)} tables from {len(sql_statements)} SQL statements. "
        f"Metadata cache rows written: {inserted_rows}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
