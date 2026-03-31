# 工作流报告校验结果

- passed: False
- failure_count: 4
- pass_count: 2

## Failures
- {"type": "missing_index_name", "sql_id": "sql_3", "detail": ["PRIMARY", "idx_customer_cust_id"]}
- {"type": "missing_table_name", "sql_id": "sql_3", "detail": "customer"}
- {"type": "missing_table_rows_exact", "sql_id": "sql_3", "detail": 890000}
- {"type": "missing_primary_key", "sql_id": "sql_3", "detail": ["id"]}

## Passes
- 未命中全局禁止短语
- sql_3: 未发现错误主键推断 ['cust_id']
