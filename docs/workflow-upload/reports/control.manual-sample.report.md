# 慢 SQL 分析报告

## 一、分析概述

本次分析针对示例 SQL 文件中包含的 SQL 语句进行性能评估。文件中共包含 **10** 条语句。其中，高风险 SQL 语句有 **2** 条，中风险 SQL 语句有 **5** 条，低风险 SQL 语句有 **3** 条，无风险 SQL 语句有 **0** 条。中高风险语句占比 **70%**。

主要性能风险集中于 **缺失索引的查询、使用 SELECT * 获取非必要字段、大数据量排序与去重、全表扫描** 等操作。这些 SQL 若在生产环境执行，预计将对数据库的 **IO/CPU** 造成显著压力，存在引发系统性性能瓶颈的风险。

## 二、整体风险评估等级

- 高风险 ■ (存在严重缺陷，可能导致服务不可用)
- 中风险 □ (存在明显性能问题，需纳入优化计划)
- 低风险 □ (性能表现可接受，或问题可忽略)

## 三、分析结果详情

#

## （一）高风险 SQL 详情分析

#

### 高风险 SQL1

- 原始SQL：`select distinct offer_id, prod_offer_inst_id from inf_bc_tran_offer where agreement_id = 58567380 and order_item_id = 232506193536782 order by prod_offer_inst_id`
- 风险等级：高风险
- 分析结果：
 1. **表基础信息**：表 `inf_bc_tran_offer`，DDL 未提供，推测 `agreement_id` 和 `order_item_id` 为关联关键字段。
 2. **索引使用预判**：提供的元数据中无索引信息。该查询包含两个等值过滤条件和一个排序字段。若无复合索引 `(agreement_id, order_item_id, prod_offer_inst_id)`，MySQL 将无法利用索引直接完成过滤和排序。
 3. **性能风险点**：
    - **全表扫描 + 文件排序**：在缺乏索引的情况下，数据库需扫描全表查找匹配行，然后在内存或磁盘中进行 `DISTINCT` 去重和 `ORDER BY` 排序。
    - **临时表开销**：`DISTINCT` 操作通常需要使用临时表，若数据量大，会消耗大量 CPU 和磁盘 IO，严重拖慢响应速度。

#

### 高风险 SQL2

- 原始SQL：`select count(*) as total_count from audit_log where created_at >= '2026-03-01 00:00:00' and created_at < '2026-03-21 00:00:00' and request_path like '/api/order/%'`
- 风险等级：高风险
- 分析结果：
 1. **表基础信息**：表 `audit_log`，通常日志表数据增长极快，属于典型的大表。
 2. **索引使用预判**：`created_at` 是范围查询，`request_path` 是前缀匹配。若无复合索引 `(created_at, request_path)`，数据库将进行全表扫描。即使有单列索引，由于范围查询和前缀匹配的组合特性，优化器可能选择全表扫描。
 3. **性能风险点**：
    - **全表扫描**：日志表通常千万级起步，全表扫描计算 `COUNT(*)` 耗时极长。
    - **锁竞争与 IO**：长时间占用 CPU 和 IO 资源，可能阻塞其他写入操作。

#

## （二）中风险 SQL 详情分析

#

### 中风险 SQL1

- 原始SQL：`select acct_id, cust_id, status_cd from account where cust_id = 20001 order by update_date desc limit 20`
- 风险等级：中风险
- 分析结果：
 1. **表基础信息**：表 `account`，假设为生产环境大表。
 2. **索引使用预判**：`WHERE cust_id = 20001` 若无索引将导致全表扫描；`ORDER BY update_date` 若索引不包含该字段，需进行 `Filesort`。
 3. **性能风险点**：在大数据量下，全表扫描 + 文件排序的组合极易导致查询延迟飙升。缺少 `(cust_id, update_date)` 复合索引是主要瓶颈。

#

### 中风险 SQL2

- 原始SQL：`select prod_inst_id, owner_cust_id, status_cd from inf_bc_prod_inst where owner_cust_id = 20001 order by update_date desc limit 50`
- 风险等级：中风险
- 分析结果：
 1. **表基础信息**：表 `inf_bc_prod_inst`，通常此类表为产品实例表，数据量较大。
 2. **索引使用预判**：`WHERE owner_cust_id = 20001` 若无索引直接全表扫描；`ORDER BY update_date` 面临排序字段未命中索引的问题。
 3. **性能风险点**：存在“过滤字段无索引”及“排序字段无索引覆盖”的双重风险。在数据量增长后，`Filesort` 开销将成为主要性能杀手。

#

### 中风险 SQL3

- 原始SQL：`select * from inf_bc_order_item where agreement_id = 58567380 and cust_order_id = 8232506193670608 order by item_sequence`
- 风险等级：中风险
- 分析结果：
 1. **表基础信息**：表 `inf_bc_order_item`，订单明细表，通常数据量极大且增长快。
 2. **SQL 语法适配性**：使用了 `SELECT *`。若表中包含大文本字段，会显著增加网络传输量和内存消耗。
 3. **索引使用预判**：双条件等值查询必须依赖复合索引 `(agreement_id, cust_order_id)` 才能避免全表扫描。
 4. **性能风险点**：`SELECT *` 在大宽表中是典型反模式；缺乏针对联合查询条件的复合索引可能导致严重的 IO 等待。

#

### 中风险 SQL4

- 原始SQL：`select * from inf_bc_prod_inst_acct_rel where acct_id = 10001 and status_cd = '1000'`
- 风险等级：中风险
- 分析结果：
 1. **表基础信息**：表 `inf_bc_prod_inst_acct_rel`，关联账户与产品实例，数据量可能较大。
 2. **SQL 语法适配性**：使用 `SELECT *`，若表中包含大文本字段，会增加网络传输和内存消耗。
 3. **索引使用预判**：若 `acct_id` 或 `status_cd` 无索引，将导致全表扫描。即使有单列索引，第二个条件可能需要回表过滤。
 4. **性能风险点**：若只有单列索引，需回表获取所有字段，当匹配行数较多时，随机 IO 压力大。

#

### 中风险 SQL5

- 原始SQL：`select * from inf_bc_offer_inst where owner_cust_id = 20001 and status_cd = '1000' order by create_date desc limit 100`
- 风险等级：中风险
- 分析结果：
 1. **表基础信息**：表 `inf_bc_offer_inst`，存储优惠实例，可能有大量历史数据。
 2. **索引使用预判**：若无复合索引 `(owner_cust_id, status_cd, create_date)`，MySQL 无法利用索引直接排序。
 3. **性能风险点**：数据库需先查出所有满足条件的记录，然后在内存/磁盘排序，最后取前 100 条。若匹配数据量极大，排序成本依然很高。

#

## （三）低风险 SQL 详情分析

#

### 低风险 SQL1

- 原始SQL：`select * from account where acct_id = 1`
- 风险等级：低风险
- 分析结果：
 1. **分析**：通常 `acct_id` 作为主键或唯一键的可能性极大。若是主键查询，MySQL 可直接通过聚簇索引定位单行记录，效率极高。
 2. **建议**：确认 `acct_id` 是否为主键。若非主键，建议添加索引以避免全表扫描。

#

### 低风险 SQL2

- 原始SQL：`select * from customer where cust_id = 20001`
- 风险等级：低风险
- 分析结果：
 1. **分析**：`cust_id` 通常是 `customer` 表的主键。单表主键等值查询属于数据库最基础的高效操作。
 2. **建议**：尽管风险低，仍建议遵循“最小化字段原则”，将 `SELECT *` 改为具体业务所需字段。

#

### 低风险 SQL3

- 原始SQL：`select * from audit_log where user_id = 10001 order by created_at desc limit 100`
- 风险等级：低风险
- 分析结果：
 1. **分析逻辑**：该查询包含明确的 `LIMIT 100` 限制。即使 `user_id` 没有索引，现代 MySQL 优化器在处理 `ORDER BY ... LIMIT` 时，若数据量不是特别巨大，可能会采用快速扫描策略。
 2. **结论**：结构简单，有分页限制，视为低风险，但仍建议添加 `(user_id, created_at)` 索引以臻完美。

## 四、共性问题和优化建议

| 问题类别 | 出现频率 | 整改建议 |
|----------------|----------|--------------------------------------------------------------------------|
| 索引缺失 | 高 | 1. **紧急创建复合索引**以覆盖过滤和排序字段。<br>- 针对排序 + 过滤场景：`CREATE INDEX idx_account_cust_update ON account(cust_id, update_date DESC);`<br>- 针对多条件等值查询：`CREATE INDEX idx_order_item_agree_cust ON inf_bc_order_item(agreement_id, cust_order_id);`<br>- 针对日志统计：`CREATE INDEX idx_created_path ON audit_log (created_at, request_path);`<br>- 针对去重排序：`CREATE INDEX idx_agree_order_prod ON inf_bc_tran_offer (agreement_id, order_item_id, prod_offer_inst_id);` |
| SQL 写法不当 | 高 | 1. **禁止 SELECT \***：所有查询应明确列出所需字段，减少回表开销和网络传输。<br>2. **优化 COUNT 查询**：对于大日志表的统计，考虑使用异步预计算表或估算值，避免实时全表扫描。<br>3. **避免隐式类型转换**：确保传入的参数类型与数据库字段定义类型严格一致，防止索引失效。 |
| 潜在锁风险 | 中 | 1. 虽然当前多为查询，但若后续涉及 `UPDATE` 或 `DELETE` 配合此类无索引条件，将导致表锁或大量行锁。务必先优化索引再执行写操作。<br>2. 大事务规避：若基于查询结果进行批量更新，务必在业务低峰期执行。 |
| 架构设计问题 | 中 | 1. **读写分离与归档**：`audit_log` 表建议实施冷热数据分离，将历史数据归档。<br>2. **引入 OLAP 引擎**：对于复杂的统计分析（如范围查询 + 模糊匹配），建议同步数据到 Elasticsearch 或 ClickHouse 处理，保护 MySQL 主库交易性能。<br>3. **缓存策略**：对于高频访问的订单明细或配置表，评估引入 Redis 缓存热点数据。 |
output
接下来，将为您导出PDF模板，请您稍等。