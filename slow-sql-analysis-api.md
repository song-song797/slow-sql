# 慢 SQL 导入接口文档

## 1. 说明

这版按你说的“提交给后端导入 API”的风格，改成了 **snake_case**，核心 SQL 字段使用：

- `sql_txt`

当前目录没有现成接口定义，所以以下内容是**按常见慢 SQL 导入接口格式整理的可用模板**，适合先拿去和后端对字段。

需要后端最终确认的项：

- 实际接口路径
- 鉴权方式
- 返回码规范
- 是否支持批量导入

---

## 2. 接口定义

- 请求方式：`POST`
- Content-Type：`application/json`
- 接口路径：`/api/slow_sql/import`

可选路径风格：

- `/api/slow-sql/import`
- `/api/sql/slow/import`
- `/internal/slow_sql/import`

---

## 3. 接口用途

用于把慢 SQL 样本导入后端，供后端后续做：

- 慢 SQL 识别
- 根因分析
- 优化建议生成
- 索引建议生成
- 统计归档和巡检

---

## 4. 请求体结构

### 4.1 标准请求体

```json
{
  "request_id": "b6d2f6aa-9f1c-4b8d-bf58-8d0b2b74f001",
  "source": "manual",
  "db_type": "mysql",
  "db_version": "8.0.36",
  "instance_name": "prod-order-mysql-01",
  "database_name": "order_db",
  "schema_name": "order_db",
  "sql_txt": "SELECT * FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20",
  "sql_template": "SELECT * FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20",
  "bind_params": [
    {
      "name": "user_id",
      "type": "BIGINT",
      "value": "10001"
    },
    {
      "name": "status",
      "type": "VARCHAR",
      "value": "PAID"
    }
  ],
  "avg_cost_ms": 842.31,
  "max_cost_ms": 2315.48,
  "min_cost_ms": 116.22,
  "p95_cost_ms": 1804.13,
  "exec_count": 127,
  "rows_examined": 185000,
  "rows_returned": 20,
  "lock_wait_ms": 0,
  "tmp_table_count": 1,
  "sample_time": "2026-03-21T10:30:00+08:00",
  "start_time": "2026-03-21T10:00:00+08:00",
  "end_time": "2026-03-21T10:30:00+08:00",
  "explain_format": "text",
  "explain_content": "EXPLAIN SELECT * FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20",
  "table_name": "t_order",
  "table_row_count": 5280000,
  "index_info": [
    "PRIMARY(id)",
    "idx_user_id(user_id)",
    "idx_status(status)",
    "idx_create_time(create_time)"
  ],
  "module_name": "order-service",
  "api_name": "/api/order/list",
  "environment": "prod",
  "expected_sla_ms": 200,
  "tags": {
    "app": "order-center",
    "owner": "trade-team"
  }
}
```

---

## 5. 字段说明

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `request_id` | string | 否 | 请求唯一标识 |
| `source` | string | 否 | 数据来源，如 `manual`、`apm`、`slow_log` |
| `db_type` | string | 是 | 数据库类型，如 `mysql`、`postgresql` |
| `db_version` | string | 否 | 数据库版本 |
| `instance_name` | string | 否 | 实例名 |
| `database_name` | string | 是 | 数据库名 |
| `schema_name` | string | 否 | schema 名 |
| `sql_txt` | string | 是 | 原始 SQL 文本 |
| `sql_template` | string | 否 | 参数归一化后的 SQL 模板 |
| `bind_params` | array | 否 | SQL 绑定参数 |
| `avg_cost_ms` | number | 建议 | 平均耗时，毫秒 |
| `max_cost_ms` | number | 否 | 最大耗时 |
| `min_cost_ms` | number | 否 | 最小耗时 |
| `p95_cost_ms` | number | 否 | P95 耗时 |
| `exec_count` | integer | 否 | 执行次数 |
| `rows_examined` | integer | 否 | 扫描行数 |
| `rows_returned` | integer | 否 | 返回行数 |
| `lock_wait_ms` | number | 否 | 锁等待耗时 |
| `tmp_table_count` | integer | 否 | 临时表次数 |
| `sample_time` | string | 否 | 样本采集时间 |
| `start_time` | string | 否 | 统计开始时间 |
| `end_time` | string | 否 | 统计结束时间 |
| `explain_format` | string | 否 | 执行计划格式，如 `text`、`json` |
| `explain_content` | string | 建议 | 执行计划内容 |
| `table_name` | string | 否 | 主表名 |
| `table_row_count` | integer | 否 | 表行数 |
| `index_info` | array | 否 | 当前索引信息 |
| `module_name` | string | 否 | 所属模块 |
| `api_name` | string | 否 | 所属接口 |
| `environment` | string | 否 | 环境，如 `prod`、`test` |
| `expected_sla_ms` | number | 否 | 期望 SLA |
| `tags` | object | 否 | 扩展标签 |

---

## 6. 最小可用导入格式

如果你们后端现在只是先接入导入能力，建议先收下面这几个核心字段：

```json
{
  "db_type": "mysql",
  "database_name": "order_db",
  "sql_txt": "SELECT * FROM t_order WHERE user_id = 10001 ORDER BY create_time DESC LIMIT 20",
  "avg_cost_ms": 842.31,
  "rows_examined": 185000,
  "rows_returned": 20
}
```

这版优点是：

- 字段少
- 容易联调
- 后端 DTO 容易先落下来

---

## 7. 返回体建议

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "request_id": "b6d2f6aa-9f1c-4b8d-bf58-8d0b2b74f001",
    "import_success": true,
    "slow_sql": true,
    "severity": "high",
    "summary": "SQL 存在大范围扫描和排序代价偏高问题",
    "root_causes": [
      "缺少联合索引",
      "ORDER BY 未命中合适索引",
      "SELECT * 导致额外 IO"
    ],
    "suggestions": [
      "建立联合索引 (user_id, status, create_time)",
      "避免 SELECT *，仅查询必要字段"
    ],
    "rewrite_sql": "SELECT id, order_no, amount, status, create_time FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20"
  }
}
```

---

## 8. 校验规则建议

后端至少建议校验：

1. `db_type` 不能为空
2. `database_name` 不能为空
3. `sql_txt` 不能为空
4. 耗时、扫描行数等数值字段不能小于 `0`
5. 时间字段必须是合法时间格式
6. `sql_txt` 建议限制最大长度，例如 `64KB`

---

## 9. cURL 示例

```bash
curl -X POST "http://localhost:8080/api/slow_sql/import" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "mysql",
    "database_name": "order_db",
    "sql_txt": "SELECT * FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20",
    "avg_cost_ms": 842.31,
    "rows_examined": 185000,
    "rows_returned": 20
  }'
```

---

## 10. 建议直接发给后端的版本

下面这段可以直接给后端做入参定义：

```json
{
  "db_type": "mysql",
  "database_name": "order_db",
  "sql_txt": "SELECT * FROM t_order WHERE user_id = ? AND status = ? ORDER BY create_time DESC LIMIT 20",
  "bind_params": [
    {
      "name": "user_id",
      "type": "BIGINT",
      "value": "10001"
    },
    {
      "name": "status",
      "type": "VARCHAR",
      "value": "PAID"
    }
  ],
  "avg_cost_ms": 842.31,
  "max_cost_ms": 2315.48,
  "exec_count": 127,
  "rows_examined": 185000,
  "rows_returned": 20,
  "sample_time": "2026-03-21T10:30:00+08:00",
  "explain_format": "text",
  "explain_content": "EXPLAIN ...",
  "module_name": "order-service",
  "api_name": "/api/order/list",
  "environment": "prod"
}
```

---

## 11. 当前假设

这版是基于下面这些假设整理的，避免无声拍板：

- 你们导入接口更偏向 `snake_case`
- SQL 原文字段名是 `sql_txt`
- 后端先需要一份“可定义 DTO / API 入参”的文档，而不是数据库设计文档

如果你们后端实际上要求的是：

- 批量数组导入
- 只有 `sql_txt` 一个核心字段，其他都不要
- 固定字段名比如 `db_name`、`cost`、`sql_id`

我可以继续帮你收成那一版。
