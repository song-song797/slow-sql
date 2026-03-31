# API 接口设计

## 基础信息

- **Base URL**: `/api/v1`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 接口列表

### 1. 慢 SQL 记录相关

#### 1.1 检索慢 SQL 记录

```
GET /api/v1/slow-sql/records
```

**请求参数**:

```typescript
{
  keyword?: string;              // 关键词
  dbname?: string;         // 数据库名
  tableName?: string;            // 表名
  query_time_min?: number;      // 最小执行时间
  query_time_max?: number;      // 最大执行时间
  timestamp_start?: string;            // 开始时间 (ISO 8601)
  timestamp_end?: string;              // 结束时间 (ISO 8601)
  status?: string;               // 状态
  riskLevel?: string;            // 风险等级
  applicationName?: string;      // 应用名称
  page: number;                  // 页码
  pageSize: number;              // 每页数量
  sortBy?: string;               // 排序字段
  sortOrder?: 'asc' | 'desc';    // 排序方向
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid-001",
        "query": "SELECT * FROM users WHERE ...",
        "query_time": 1250,
        "dbname": "test_db",
        "tableNames": ["users", "orders"],
        "status": "pending",
        "timestamp": "2024-01-15T10:30:25Z"
      }
    ],
    "total": 156,
    "page": 1,
    "pageSize": 10,
    "totalPages": 16
  }
}
```

#### 1.2 获取记录详情

```
GET /api/v1/slow-sql/records/:id
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "uuid-001",
    "query": "SELECT * FROM users WHERE ...",
    "query_time": 1250,
    "executionPlan": {
      "id": 1,
      "selectType": "SIMPLE",
      "table": "users",
      "type": "ALL",
      "rows": 10000
    },
    "rowsExamined": 10000,
    "rowsSent": 100,
    "status": "completed"
  }
}
```

#### 1.3 批量删除记录

```
DELETE /api/v1/slow-sql/records
```

**请求体**:

```json
{
  "ids": ["uuid-001", "uuid-002"]
}
```

### 2. 分析相关

#### 2.1 执行分析

```
POST /api/v1/analysis/analyze
```

**请求体**:

```json
{
  "recordIds": ["uuid-001", "uuid-002"],
  "analysisType": "auto"
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "分析任务已提交",
  "data": {
    "taskId": "task-uuid-001",
    "status": "processing"
  }
}
```

#### 2.2 获取分析结果

```
GET /api/v1/analysis/results/:id
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "result-uuid-001",
    "recordId": "uuid-001",
    "rootCause": "缺少索引导致全表扫描",
    "optimizationSuggestions": [
      {
        "suggestionType": "index",
        "description": "建议在 users.email 字段上创建索引",
        "priority": 9,
        "estimatedImprovement": 80,
        "sqlExample": "CREATE INDEX idx_email ON users(email);"
      }
    ],
    "riskLevel": "high",
    "pdfPath": "/reports/result-uuid-001.pdf",
    "pdfSize": 2621440
  }
}
```

#### 2.3 获取分析结果列表

```
GET /api/v1/analysis/results
```

**请求参数**:

```typescript
{
  recordId?: string;      // 关联的记录 ID
  riskLevel?: string;     // 风险等级
  timestamp_start?: string;     // 开始时间
  timestamp_end?: string;       // 结束时间
  page: number;
  pageSize: number;
}
```

#### 2.4 下载 PDF 报告

```
GET /api/v1/analysis/results/:id/pdf
```

**响应**: PDF 文件流

### 3. 统计相关

#### 3.1 获取统计信息

```
GET /api/v1/statistics
```

**请求参数**:

```typescript
{
  startDate: string;      // 开始日期
  endDate: string;        // 结束日期
  groupBy?: 'day' | 'week' | 'month';
}
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalSlowSqls": 156,
    "avgExecutionTime": 1250,
    "query_time_max": 5000,
    "mostFrequentTables": [
      { "tableName": "users", "count": 45 },
      { "tableName": "orders", "count": 32 }
    ],
    "mostFrequentOperations": [
      { "operation": "SELECT", "count": 120 },
      { "operation": "UPDATE", "count": 25 }
    ]
  }
}
```

### 4. 导出相关

#### 4.1 导出记录

```
POST /api/v1/export/records
```

**请求体**:

```json
{
  "ids": ["uuid-001", "uuid-002"],  // 空数组表示导出全部
  "format": "excel" | "csv"
}
```

**响应**: 文件流

## 错误码定义

| 错误码 | 说明           |
| ------ | -------------- |
| 200    | 成功           |
| 400    | 请求参数错误   |
| 401    | 未授权         |
| 403    | 无权限         |
| 404    | 资源不存在     |
| 500    | 服务器内部错误 |

## 错误响应格式

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": null,
  "errors": [
    {
      "field": "page",
      "message": "页码必须大于 0"
    }
  ]
}
```
