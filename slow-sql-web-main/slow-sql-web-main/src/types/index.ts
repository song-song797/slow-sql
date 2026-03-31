/**
 * 慢 SQL 分析系统 - TypeScript 类型定义
 */

export * from "./analysis-search";

// 执行计划接口
export interface ExecutionPlan {
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

// 慢 SQL 记录接口
export interface SlowSqlRecord {
  id: string;
  timestamp: number;
  upstream_addr: string; //数据库地址
  client_ip?: string;
  cmd?: string;
  query: string;
  dbname: string;
  dbuser: string;
  type?: string;
  workgroup_name?: string;
  client_port: string;
  //返回的query_time是秒为单位，但是页面展示的是毫秒
  // queryTime:number;
  query_time: number;

  is_slow_sql?: boolean;
  threshold: number;

  schemaName?: string;
  tableNames: string[];
  indexNames: string[];

  applicationName?: string;

  executionPlan?: ExecutionPlan;
  rowsExamined: number;
  rowsSent: number;
  keyUsed?: string;
  possibleKeys: string[];

  lockTime: number;
  sortRows: number;
  checkRows: number;
  status?: "pending" | "analyzing" | "completed" | "failed";
  analysisStatus?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ClusteredSqlRecord {
  cluster_id: string;
  template_sql: string;
  sample_sql: string;
  dbname: string;
  dbuser?: string;
  type?: string;
  upstream_addr?: string;
  cluster_count: number;
  first_timestamp: number;
  min_query_time_ms?: number | null;
  avg_query_time_ms?: number | null;
  max_query_time_ms?: number | null;
  latest_timestamp: number;
  is_slow_sql?: boolean | null;
}

// 优化建议接口
export interface OptimizationSuggestion {
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

//请求分析接口
export interface AnalysisParam {
  sql: string;
  dbname: string;
  table_name: string;
  db_ip: string;
  db_port: 0;
  table_rows: 0;
  ddl: string;
}

export interface AnalysisResultMetadataSummary {
  matched_tables_count: number;
  auto_fetched_tables_count: number;
  missing_tables_count: number;
  fetch_errors_count: number;
  sql_observation_count: number;
  tables_with_ddl_count: number;
  tables_with_indexes_count: number;
}

export interface AnalysisResultAuthoritativeTable {
  table_name?: string | null;
  table_rows_exact?: number | null;
  index_count: number;
  has_indexes: boolean;
  ddl_available: boolean;
}

export interface AnalysisResultInputDiagnostics {
  workflow_input_mode: string;
  workflow_input_length: number;
  compaction_level: string;
  matched_tables_count: number;
  tables_with_ddl_count: number;
  tables_with_indexes_count: number;
  authoritative_tables: AnalysisResultAuthoritativeTable[];
}

export interface AnalysisResultConsistencyFlags {
  report_mentions_zero_rows_despite_positive_rows: boolean;
  report_mentions_missing_indexes_despite_indexes_present: boolean;
  report_claims_metadata_missing_but_input_had_metadata: boolean;
  report_used_unknown_when_authoritative_value_present: boolean;
}

export interface AnalysisResultPayload {
  provider: string;
  db_type?: string | null;
  report_url?: string | null;
  risk_level?: number | null;
  summary: string;
  report_content?: string | null;
  messages: string[];
  metadata_summary: AnalysisResultMetadataSummary;
  input_diagnostics: AnalysisResultInputDiagnostics;
  consistency_flags: AnalysisResultConsistencyFlags;
}

export interface DataSource {
  id: number;
  name: string;
  db_type: string;
  host: string;
  port: number;
  db_name: string;
  username: string;
  enabled: boolean;
  last_test_status?: string | null;
  last_test_message?: string | null;
  last_test_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DataSourceFormValues {
  name: string;
  db_type: string;
  host: string;
  port: number;
  db_name: string;
  username: string;
  password?: string;
  enabled: boolean;
}

export interface DataSourceTestResult {
  success: boolean;
  message: string;
  db_version?: string | null;
  table_count?: number | null;
  last_test_status: string;
  last_test_at?: string | null;
}

// 分析结果接口
export interface AnalysisResult {
  task_id: string; // 任务ID
  status: string; // 状态：pending, processing, completed, failed
  report_url?: string | null; // PDF 报告 URL
  sql_text?: string[]; // 涉及的 SQL 语句列表
  error_message?: string | null; // 错误信息
  risk_level: number; // 风险等级：1=低，2=中，3=高，4=严重
  created_at?: string; // 创建时间，ISO 8601 格式，如 "2025-12-24T17:11:03"
  finished_at?: string; // 完成时间，ISO 8601 格式，如 "2025-12-24T09:11:57"
  message?: string | null;
  analysis_result?: AnalysisResultPayload | null;
  data_source_id?: number | null;
  data_source_name?: string | null;
  target_db_type?: string | null;
  target_host?: string | null;
  target_port?: number | null;
  target_db_name?: string | null;
}

export interface AnalysisTaskDetail extends AnalysisResult {}

export interface AnalysisTaskHideResponse {
  task_id: string;
  hidden: boolean;
  message: string;
}

export interface AnalysisTaskBatchHideResponse {
  hidden_count: number;
  task_ids: string[];
  message: string;
}

// 检索条件接口
export interface SearchCriteria {
  keyword?: string;
  dbname?: string;
  tableName?: string;
  query_time_min?: number;
  query_time_max?: number;
  timestamp_start?: string;
  timestamp_end?: string;
  status?: "pending" | "analyzing" | "completed" | "failed" | "";
  riskLevel?: "low" | "medium" | "high" | "";
  applicationName?: string;
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  type?: string;
  is_slow_sql?: boolean;
  upstream_addr?: string; //数据库地址
  dbuser?: string;
}

// 检索结果接口
export interface SearchResult<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number; // 统一使用 pageSize
  totalPages?: number;
  totalRecordCount?: number;
  scannedRecordCount?: number;
  truncated?: boolean;
}

// 统计信息接口
export interface SqlStatistics {
  date: string;
  totalSlowSqls: number;
  avgExecutionTime: number;
  query_time_max: number;
  mostFrequentTables: Array<{ tableName: string; count: number }>;
  mostFrequentOperations: Array<{ operation: string; count: number }>;
}

// API 响应接口
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

// 分页参数接口
export interface PaginationParams {
  page: number;
  pageSize: number;
}

// 排序参数接口
export interface SortParams {
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}
