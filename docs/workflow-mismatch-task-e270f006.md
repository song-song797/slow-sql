# 远端 Workflow 元数据失真对照说明

## 1. 任务信息
- 任务 ID: `e270f006-7d20-48e1-94d8-61d6658297c7`
- 分析日期: `2026-03-18`
- 在线 workflow: `fb594dae47c5440dbea05725ebec6674`
- 输入模式: `sql_text`
- 输入长度: `3488`
- 压缩档位: `full`

## 2. 本地权威元数据事实
本地 `analysis_context` 命中了 `account` 表元数据，且这些事实已经成功写入提交给远端的 `sql_text`：

- `table_name = account`
- `db_type = mysql`
- `db_name = CUSDBX`
- `db_ip = 127.0.0.1`
- `db_port = 3306`
- `table_rows_exact = 150000`
- `index_count = 4`
- `has_indexes = yes`
- `index_names = idx_account_acct_id_cust_id, idx_account_acct_id, idx_account_seq_nbr, idx_account_cust_id`
- `ddl_available = yes`
- `db_version = shadow-mysql-8.0`

本地一致性检测结果：

- `report_mentions_zero_rows_despite_positive_rows = true`
- `report_mentions_missing_indexes_despite_indexes_present = true`
- `report_claims_metadata_missing_but_input_had_metadata = false`
- `report_used_unknown_when_authoritative_value_present = false`

## 3. 实际提交给远端的 `sql_text` 关键片段
以下内容来自本地数据库中保存的真实提交文本，不是人工整理的二次描述。

### 3.1 分析规则
```text
## 分析规则
- 以下“权威表元数据摘要”来自本地元数据缓存或数据源补拉结果，优先级高于模型自行推测。
- 若 table_rows_exact 为数值，禁止改写为 0、未知或空值。
- 若 index_count > 0 或 has_indexes = yes，禁止写成“索引为空”“无索引”或“无法确认是否有索引”。
- 若 ddl_available = yes，禁止写成“DDL 为空”或“未提供 DDL”。
- 若无法确认，请仅依据“元数据缺失说明”描述，不得凭空补默认值。
```

### 3.2 权威表元数据摘要
```text
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
```

### 3.3 SQL 列表
````text
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
````

### 3.4 SQL 观测统计
````text
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
````

### 3.5 原始 DDL 附录关键信息
```sql
CREATE TABLE `account` (
  `acct_billing_type` varchar(64) DEFAULT NULL,
  `acct_cd` varchar(64) DEFAULT NULL,
  `acct_id` bigint DEFAULT NULL,
  ...
  KEY `idx_account_acct_id_cust_id` (`acct_id`,`cust_id`),
  KEY `idx_account_acct_id` (`acct_id`),
  KEY `idx_account_seq_nbr` (`seq_nbr`),
  KEY `idx_account_cust_id` (`cust_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

### 3.6 元数据缺失说明
```text
## 元数据缺失说明
- 本次分析所涉及的表元数据已完整命中
```

## 4. 远端生成的错误结论
以下内容来自远端返回正文，和本地权威元数据明显冲突：

```text
1. 表基础信息：表名为 `account`，当前元数据显示行数为 0（注：生产环境通常远大于此，但基于给定信息按小表或空表处理）。主键信息未在 DDL 中明确提供，但 `acct_id` 作为查询条件极可能为主键或唯一键。

3. 索引使用预判：查询条件为 `acct_id = 1`（等值查询）。在正常的数据库设计中，`acct_id` 通常为主键（聚簇索引）或建有唯一索引。若存在该索引，查询将直接通过索引定位单行记录，时间复杂度为 O(1)。即使无索引，鉴于元数据表明表行数为 0，全表扫描成本也可忽略不计。
```

同时，远端在“共性问题和优化建议”里还给出了这类建议：

```text
建议确认该字段是否已建立主键或索引。若未建立，执行：
ALTER TABLE account ADD PRIMARY KEY (acct_id);
或 CREATE INDEX idx_account_acct_id ON account(acct_id);
```

这与输入中的权威事实也冲突，因为输入已明确给出：

- `index_count = 4`
- `has_indexes = yes`
- `index_names` 非空
- DDL 附录中也明确存在 4 个 `KEY`

## 5. 明确冲突点
### 冲突 A: 行数被错误改写为 0
输入事实：
- `table_rows_exact = 150000`

远端输出：
- “当前元数据显示行数为 0”
- “鉴于元数据表明表行数为 0”

结论：
- 远端没有正确消费 `table_rows_exact`
- 更像是把“缺失数值”错误兜底成了 `0`，或被某个中间抽取步骤覆盖

### 冲突 B: 已存在索引却被当成不确定/可能无索引
输入事实：
- `index_count = 4`
- `has_indexes = yes`
- `index_names` 已明确列出 4 个索引
- DDL 附录里也明确有 4 个 `KEY`

远端输出：
- “主键信息未在 DDL 中明确提供”
- “acct_id 极可能为主键或唯一键”
- “若存在该索引……”
- 共性建议继续要求“确认是否已建立主键或索引”

结论：
- 远端没有把“索引已存在”当作确定事实使用
- 更像是退回到了通用启发式分析，而不是读取输入中的权威摘要

## 6. 基于证据的定位结论
当前更像是远端 workflow 内部的抽取/分析节点存在以下问题之一：

1. 没有优先读取“权威表元数据摘要”，而是主要依赖自由文本推测
2. 某个中间抽取步骤把缺失值默认补成了 `0`
3. 某个节点没有正确消费 DDL 附录中的索引定义
4. 即使读取到了索引信息，后续总结节点仍被通用慢 SQL 提示词覆盖，输出了模板化建议

## 7. 建议调 workflow 的方向
### 必调
1. 强制先解析 `权威表元数据摘要`，再进入风险分析
2. 禁止把缺失数值默认补成 `0`
3. 当 `index_count > 0` 或 `has_indexes = yes` 时，禁止输出“索引为空 / 无法确认是否有索引 / 请确认是否建索引”
4. 当 `ddl_available = yes` 时，禁止输出“DDL 未提供 / DDL 为空”

### 建议补充到提示词里的硬约束
```text
如果输入中存在 table_rows_exact，则必须原样使用，不得改写为 0、未知或空值。
如果输入中存在 index_count > 0 或 has_indexes = yes，则必须认定该表存在索引，不得输出“索引为空”“无法确认是否有索引”“建议先确认是否建索引”。
如果输入中的“权威表元数据摘要”和模型推测冲突，以权威表元数据摘要为准。
```

### 建议观察的中间节点
如果 workflow 支持看中间结果，建议重点检查：

1. `sql_text` 首次进入 LLM/抽取节点后的结构化结果
2. 行数字段是否在中间步骤被写成 `0`
3. 索引字段是否在中间步骤被丢失
4. 最终总结节点是否忽略了已抽取出的索引/行数事实

## 8. 当前本地系统状态
本地系统已经做到以下几点：

- 已将权威元数据前置到 `sql_text`
- 已在详情页和结果页标出“远端报告与本地权威元数据不一致”
- 已保留输入诊断信息，便于继续联调

因此，当前最值得投入的方向不是继续查本地取数，而是调远端 workflow 的元数据抽取和总结提示词。
