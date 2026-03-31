/**
 * 分析结果检索条件接口
 */

export interface AnalysisSearchCriteria {
  keyword?: string;
  task_id?: string;
  riskLevel?: "low" | "medium" | "high" | "";
  timestamp_start?: string;
  timestamp_end?: string;
  page: number;
  pageSize: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}
