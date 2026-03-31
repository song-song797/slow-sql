# 工作流报告校验结果

- passed: False
- failure_count: 3
- pass_count: 3

## Failures
- {"type": "forbidden_phrase", "detail": "无索引"}
- {"type": "missing_table_rows_exact", "sql_id": "sql_3", "detail": 890000}
- {"type": "wrong_primary_key_claim", "sql_id": "sql_3", "detail": ["cust_id"]}

## Passes
- sql_3: 命中至少一个要求的索引名
- sql_3: 命中表名 customer
- sql_3: 命中主键 ['id']
