# 工作流报告校验结果

- passed: False
- failure_count: 4
- pass_count: 3

## Failures
- {"type": "forbidden_phrase", "detail": "无索引"}
- {"type": "forbidden_phrase", "detail": "未提供 DDL"}
- {"type": "missing_index_name", "sql_id": "sql_10", "detail": ["PRIMARY", "idx_audit_log_created_at", "idx_audit_log_request_path"]}
- {"type": "missing_table_rows_exact", "sql_id": "sql_10", "detail": 8600000}

## Passes
- sql_10: 命中表名 audit_log
- sql_10: 命中主键 ['id']
- sql_10: 未发现错误主键推断 ['user_id', 'request_path']
