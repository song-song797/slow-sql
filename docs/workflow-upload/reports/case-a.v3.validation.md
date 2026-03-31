# 工作流报告校验结果

- passed: False
- failure_count: 2
- pass_count: 4

## Failures
- {"type": "missing_table_rows_exact", "sql_id": "sql_3", "detail": 890000}
- {"type": "wrong_primary_key_claim", "sql_id": "sql_3", "detail": ["cust_id"]}

## Passes
- 未命中全局禁止短语
- sql_3: 命中至少一个要求的索引名
- sql_3: 命中表名 customer
- sql_3: 命中主键 ['id']
