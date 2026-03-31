# 慢 SQL 分析系统 - 数据模型设计

## 1. 慢 SQL 记录表 (slow_sql_records)

### 基本信息

- **id**: 唯一标识符 (UUID 或自增 ID)
- **sql_text**: SQL 语句全文
- **execution_time**: 执行时间（毫秒）
- **threshold**: 慢 SQL 阈值（毫秒）
- **record_time**: 记录时间（时间戳）

### 数据库上下文信息

- **database_name**: 数据库名称
- **schema_name**: Schema 名称
- **table_names**: 涉及的表名（JSON 数组）
- **index_names**: 使用的索引（JSON 数组）

### 执行环境信息

- **upstream_addr**: 数据库主机地址
- **port**: 数据库端口
- **user_name**: 执行用户
- **application_name**: 应用名称
- **client_ip**: 客户端 IP 地址

### 执行计划信息

- **execution_plan**: 执行计划（JSON 格式）
- **rows_examined**: 扫描行数
- **rows_sent**: 返回行数
- **key_used**: 使用的索引键
- **possible_keys**: 可能的索引键（JSON 数组）

### 性能指标

- **query_time**: 查询时间（秒）
- **lock_time**: 锁等待时间（秒）
- **sort_rows**: 排序行数
- **check_rows**: 检查行数

### 状态信息

- **status**: 状态（pending/analyzing/completed/failed）
- **analysis_status**: 分析状态
- **created_at**: 创建时间
- **updated_at**: 更新时间

## 2. 分析结果表 (analysis_results)

### 基本信息

- **id**: 唯一标识符
- **record_id**: 关联的慢 SQL 记录 ID
- **analysis_time**: 分析时间（时间戳）

### 分析结果

- **analysis_type**: 分析类型（auto/manual）
- **root_cause**: 根本原因分析（文本）
- **optimization_suggestions**: 优化建议（JSON 数组）
- **risk_level**: 风险等级（low/medium/high/critical）

### 优化建议详情

每个建议包含：

- **suggestion_type**: 建议类型（index/query_rewrite/table_optimization/configuration）
- **description**: 建议描述
- **priority**: 优先级（1-10）
- **estimated_improvement**: 预估改进（百分比）

### 结果文件

- **pdf_path**: PDF 分析报告路径
- **pdf_size**: PDF 文件大小（字节）
- **pdf_generated_at**: PDF 生成时间

### 元数据

- **analyzer_version**: 分析器版本
- **analysis_duration**: 分析耗时（毫秒）
- **created_at**: 创建时间
- **updated_at**: 更新时间

## 3. 数据统计表 (sql_statistics)

### 聚合统计信息

- **date**: 统计日期
- **total_slow_sqls**: 慢 SQL 总数
- **avg_execution_time**: 平均执行时间
- **max_execution_time**: 最大执行时间
- **most_frequent_tables**: 最频繁出现的表（JSON）
- **most_frequent_operations**: 最频繁的操作类型（JSON）

## 4. TypeScript 接口定义

```typescript
// 慢 SQL 记录接口
interface SlowSqlRecord {
  id: string;
  query: string;
  query_time: number;
  threshold: number;
  timestamp: number;
  dbname: string;
  schemaName?: string;
  tableNames: string[];
  indexNames: string[];
  upstream_addr: string;
  port: number;
  dbuser: string;
  applicationName?: string;
  client_ip?: string;
  executionPlan?: ExecutionPlan;
  rowsExamined: number;
  rowsSent: number;
  keyUsed?: string;
  possibleKeys: string[];
  query_time: number;
  lockTime: number;
  sortRows: number;
  checkRows: number;
  status: "pending" | "analyzing" | "completed" | "failed";
  analysisStatus?: string;
  createdAt: string;
  updatedAt: string;
}

// 执行计划接口
interface ExecutionPlan {
  id: number;
  selectType: string;
  table: string;
  type: string;
  possibleKeys: string[];
  key: string;
  keyLen: number;
  ref: string;
  rows: number;
  filtered: number;
  extra: string;
}

// 分析结果接口
interface AnalysisResult {
  id: string;
  recordId: string;
  analysisTime: number;
  analysisType: "auto" | "manual";
  rootCause: string;
  optimizationSuggestions: OptimizationSuggestion[];
  riskLevel: "low" | "medium" | "high" | "critical";
  pdfPath?: string;
  pdfSize?: number;
  pdfGeneratedAt?: string;
  analyzerVersion: string;
  analysisDuration: number;
  createdAt: string;
  updatedAt: string;
}

// 优化建议接口
interface OptimizationSuggestion {
  suggestionType:
    | "index"
    | "query_rewrite"
    | "table_optimization"
    | "configuration";
  description: string;
  priority: number;
  estimatedImprovement: number;
  sqlExample?: string;
}

// 检索条件接口
interface SearchCriteria {
  keyword?: string;
  dbname?: string;
  tableName?: string;
  query_time_min?: number;
  query_time_max?: number;
  timestamp_start?: string;
  timestamp_end?: string;
  status?: string;
  riskLevel?: string;
  applicationName?: string;
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

// 检索结果接口
interface SearchResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
```
