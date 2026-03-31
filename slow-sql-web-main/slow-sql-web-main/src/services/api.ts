import {
  AnalysisTaskBatchHideResponse,
  AnalysisTaskDetail,
  AnalysisTaskHideResponse,
  AnalysisResult,
  ClusteredSqlRecord,
  DataSource,
  DataSourceFormValues,
  DataSourceTestResult,
  SearchCriteria,
  SearchResult,
  SlowSqlRecord,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:10800";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-api-key";

export function resolveApiUrl(url: string): string {
  if (!url) {
    return url;
  }
  if (/^https?:\/\//i.test(url)) {
    return url;
  }
  const baseUrl = API_BASE_URL.replace(/\/$/, "");
  if (url.startsWith("/")) {
    return `${baseUrl}${url}`;
  }
  return `${baseUrl}/${url}`;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `API Error: ${response.statusText}`);
  }

  return response.json();
}

export async function searchSlowSqlRecords(
  criteria: SearchCriteria
): Promise<SearchResult<SlowSqlRecord>> {
  const params = new URLSearchParams();

  if (criteria.keyword) params.append("keyword", criteria.keyword);
  if (criteria.dbname) params.append("dbname", criteria.dbname);
  if (criteria.type) params.append("type", criteria.type);
  if (criteria.query_time_min !== undefined) {
    params.append("query_time_min", String(criteria.query_time_min / 1000));
  }
  if (criteria.query_time_max !== undefined) {
    params.append("query_time_max", String(criteria.query_time_max / 1000));
  }
  if (criteria.timestamp_start) params.append("timestamp_start", criteria.timestamp_start);
  if (criteria.timestamp_end) params.append("timestamp_end", criteria.timestamp_end);
  if (criteria.is_slow_sql !== undefined) params.append("is_slow_sql", String(criteria.is_slow_sql));
  if (criteria.upstream_addr) params.append("upstream_addr", criteria.upstream_addr);
  if (criteria.dbuser) params.append("dbuser", criteria.dbuser);
  if (criteria.sortBy) params.append("sort_by", criteria.sortBy);
  if (criteria.sortOrder) params.append("sort_order", criteria.sortOrder);
  params.append("page", String(criteria.page));
  params.append("page_size", String(criteria.pageSize));

  interface ApiResponse {
    total: number;
    page: number;
    page_size: number;
    total_record_count?: number;
    items: Array<Record<string, unknown>>;
  }

  const response = await request<ApiResponse>(`/api/v1/es-query?${params.toString()}`);
  const pageSize = response.page_size || criteria.pageSize || 20;
  const total = response.total || 0;

  const items: SlowSqlRecord[] = (response.items || []).map((item) => {
    const record = item as unknown as SlowSqlRecord;
    return {
      ...record,
      query_time:
        typeof record.query_time === "string"
          ? parseFloat(record.query_time) || 0
          : record.query_time || 0,
      timestamp:
        typeof record.timestamp === "string"
          ? parseInt(String(record.timestamp), 10) || 0
          : record.timestamp || 0,
    };
  });

  return {
    items,
    total,
    page: response.page || criteria.page || 1,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
    totalRecordCount: response.total_record_count,
  };
}

export async function searchClusteredSqlRecords(
  criteria: SearchCriteria,
  signal?: AbortSignal
): Promise<SearchResult<ClusteredSqlRecord>> {
  const params = new URLSearchParams();

  if (criteria.keyword) params.append("keyword", criteria.keyword);
  if (criteria.dbname) params.append("dbname", criteria.dbname);
  if (criteria.type) params.append("type", criteria.type);
  if (criteria.query_time_min !== undefined) {
    params.append("query_time_min", String(criteria.query_time_min / 1000));
  }
  if (criteria.query_time_max !== undefined) {
    params.append("query_time_max", String(criteria.query_time_max / 1000));
  }
  if (criteria.timestamp_start) params.append("timestamp_start", criteria.timestamp_start);
  if (criteria.timestamp_end) params.append("timestamp_end", criteria.timestamp_end);
  if (criteria.is_slow_sql !== undefined) params.append("is_slow_sql", String(criteria.is_slow_sql));
  if (criteria.upstream_addr) params.append("upstream_addr", criteria.upstream_addr);
  if (criteria.dbuser) params.append("dbuser", criteria.dbuser);
  if (criteria.sortBy) params.append("sort_by", criteria.sortBy);
  if (criteria.sortOrder) params.append("sort_order", criteria.sortOrder);
  params.append("page", String(criteria.page));
  params.append("page_size", String(criteria.pageSize));

  interface ApiResponse {
    total: number;
    page: number;
    page_size: number;
    total_record_count?: number;
    scanned_record_count?: number;
    truncated?: boolean;
    items: Array<Record<string, unknown>>;
  }

  const response = await request<ApiResponse>(`/api/v1/es-query/clusters?${params.toString()}`, {
    signal,
  });
  const pageSize = response.page_size || criteria.pageSize || 20;
  const total = response.total || 0;

  const items: ClusteredSqlRecord[] = (response.items || []).map((item) => {
    const record = item as unknown as ClusteredSqlRecord;
    return {
      ...record,
      cluster_count: Number(record.cluster_count || 0),
      first_timestamp:
        typeof record.first_timestamp === "string"
          ? parseInt(String(record.first_timestamp), 10) || 0
          : Number(record.first_timestamp || 0),
      min_query_time_ms:
        record.min_query_time_ms === null || record.min_query_time_ms === undefined
          ? null
          : Number(record.min_query_time_ms),
      avg_query_time_ms:
        record.avg_query_time_ms === null || record.avg_query_time_ms === undefined
          ? null
          : Number(record.avg_query_time_ms),
      max_query_time_ms:
        record.max_query_time_ms === null || record.max_query_time_ms === undefined
          ? null
          : Number(record.max_query_time_ms),
      latest_timestamp:
        typeof record.latest_timestamp === "string"
          ? parseInt(String(record.latest_timestamp), 10) || 0
          : Number(record.latest_timestamp || 0),
    };
  });

  return {
    items,
    total,
    page: response.page || criteria.page || 1,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
    totalRecordCount: response.total_record_count,
    scannedRecordCount: response.scanned_record_count,
    truncated: response.truncated,
  };
}

export async function analyzeSlowSql(
  payload:
    | Array<{
        sql: string;
        db_type?: string;
        dbname: string;
        db_ip: string;
        db_port?: number;
        source_record_id?: string;
        source_index?: string;
        template_sql?: string;
        observation_override?: {
          cluster_count: number;
          min_query_time_ms?: number | null;
          avg_query_time_ms?: number | null;
          max_query_time_ms?: number | null;
          latest_timestamp?: number | null;
        };
      }>
    | {
        data_source_id: number;
        items: Array<{
          sql: string;
          db_type?: string;
          dbname: string;
          db_ip: string;
          db_port?: number;
          source_record_id?: string;
          source_index?: string;
          template_sql?: string;
          observation_override?: {
            cluster_count: number;
            min_query_time_ms?: number | null;
            avg_query_time_ms?: number | null;
            max_query_time_ms?: number | null;
            latest_timestamp?: number | null;
          };
        }>;
      }
): Promise<{ task_id: string; status: string }> {
  return request<{ task_id: string; status: string; message: string }>(
    "/api/v1/sql-analysis/submit",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function getAnalysisResult(id: string): Promise<AnalysisResult> {
  return request<AnalysisResult>(`/api/v1/sql-analysis/report/${id}`);
}

export async function getAnalysisTaskDetail(id: string): Promise<AnalysisTaskDetail> {
  return request<AnalysisTaskDetail>(`/api/v1/sql-analysis/tasks/${id}`);
}

export async function getAnalysisResults(params: {
  task_id?: string;
  riskLevel?: string;
  start_time?: string;
  end_time?: string;
  page: number;
  pageSize: number;
}): Promise<SearchResult<AnalysisResult>> {
  const queryParams = new URLSearchParams();

  const riskLevelMap: Record<string, string> = {
    low: "1",
    medium: "2",
    high: "3",
  };

  if (params.task_id) queryParams.append("task_id", params.task_id);
  if (params.riskLevel) {
    const mappedValue = riskLevelMap[params.riskLevel.toLowerCase()];
    if (mappedValue) {
      queryParams.append("risk_level", mappedValue);
    }
  }
  if (params.start_time) queryParams.append("start_time", params.start_time);
  if (params.end_time) queryParams.append("end_time", params.end_time);
  queryParams.append("page", String(params.page));
  queryParams.append("page_size", String(params.pageSize));

  interface ApiResponse {
    total: number;
    page: number;
    page_size: number;
    totalPages?: number;
    items: AnalysisResult[];
  }

  const response = await request<ApiResponse>(
    `/api/v1/sql-analysis/tasks?${queryParams.toString()}`
  );

  return {
    items: response.items || [],
    total: response.total || 0,
    page: response.page || params.page,
    pageSize: response.page_size || params.pageSize,
    totalPages:
      response.totalPages ||
      Math.ceil((response.total || 0) / (response.page_size || params.pageSize)),
  };
}

export async function hideAnalysisTask(taskId: string): Promise<AnalysisTaskHideResponse> {
  return request<AnalysisTaskHideResponse>(`/api/v1/sql-analysis/tasks/${taskId}/hide`, {
    method: "POST",
  });
}

export async function hideAnalysisTasks(taskIds: string[]): Promise<AnalysisTaskBatchHideResponse> {
  return request<AnalysisTaskBatchHideResponse>("/api/v1/sql-analysis/tasks/hide", {
    method: "POST",
    body: JSON.stringify({ task_ids: taskIds }),
  });
}

export async function getDataSources(params?: {
  enabled?: boolean;
  db_type?: string;
  host?: string;
  port?: number;
  db_name?: string;
  last_test_status?: string;
}): Promise<{ total: number; items: DataSource[] }> {
  const queryParams = new URLSearchParams();
  if (params?.enabled !== undefined) queryParams.append("enabled", String(params.enabled));
  if (params?.db_type) queryParams.append("db_type", params.db_type);
  if (params?.host) queryParams.append("host", params.host);
  if (params?.port !== undefined) queryParams.append("port", String(params.port));
  if (params?.db_name) queryParams.append("db_name", params.db_name);
  if (params?.last_test_status) queryParams.append("last_test_status", params.last_test_status);
  const suffix = queryParams.toString() ? `?${queryParams.toString()}` : "";
  return request<{ total: number; items: DataSource[] }>(`/api/v1/data-sources${suffix}`);
}

export async function createDataSource(payload: DataSourceFormValues): Promise<DataSource> {
  return request<DataSource>("/api/v1/data-sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateDataSource(id: number, payload: Partial<DataSourceFormValues>): Promise<DataSource> {
  return request<DataSource>(`/api/v1/data-sources/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function testDataSource(id: number): Promise<DataSourceTestResult> {
  return request<DataSourceTestResult>(`/api/v1/data-sources/${id}/test`, {
    method: "POST",
  });
}

export async function syncDataSourceMetadata(id: number, tableName?: string): Promise<{ success: boolean; message: string; synced_count: number }> {
  return request<{ success: boolean; message: string; synced_count: number }>(`/api/v1/data-sources/${id}/sync-metadata`, {
    method: "POST",
    body: JSON.stringify({ table_name: tableName || null }),
  });
}

export async function enableDataSource(id: number): Promise<DataSource> {
  return request<DataSource>(`/api/v1/data-sources/${id}/enable`, {
    method: "POST",
  });
}

export async function disableDataSource(id: number): Promise<DataSource> {
  return request<DataSource>(`/api/v1/data-sources/${id}/disable`, {
    method: "POST",
  });
}

export async function downloadPdfReportsZip(taskIds: string[]): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sql-analysis/download-pdfs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify({ task_ids: taskIds }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`批量下载失败: ${response.status} ${errorText}`);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition") || "";
  const filenameMatch = contentDisposition.match(/filename="([^"]+)"/i);
  const filename = filenameMatch?.[1] || "analysis-reports.zip";

  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();

  setTimeout(() => {
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }, 100);
}

export async function downloadPdfReport(
  reportUrl: string,
  taskId: string
): Promise<void> {
  if (!reportUrl) {
    throw new Error("报告 URL 不存在");
  }

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();

    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }, 100);
  };

  const isRemoteReportUrl = /^https?:\/\//i.test(reportUrl);
  const requestUrl = isRemoteReportUrl
    ? `${API_BASE_URL}/api/v1/sql-analysis/download-pdf`
    : resolveApiUrl(reportUrl);
  const requestOptions: RequestInit = isRemoteReportUrl
    ? {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
        },
        body: JSON.stringify({ report_url: reportUrl }),
      }
    : {
        method: "GET",
        headers: {
          "X-API-Key": API_KEY,
        },
      };

  const response = await fetch(requestUrl, requestOptions);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      isRemoteReportUrl
        ? `代理下载失败: ${response.status} ${errorText}`
        : `本地报告下载失败: ${response.status} ${errorText}`
    );
  }

  const blob = await response.blob();
  triggerDownload(blob, `analysis-report-${taskId}.pdf`);
}
