# 组件设计说明

## 组件结构

```
src/
├── components/           # 可复用组件
│   ├── SearchPanel/     # 检索条件面板
│   ├── RecordTable/     # 记录表格
│   ├── StatusBadge/     # 状态标签
│   ├── RiskBadge/       # 风险等级标签
│   └── Pagination/      # 分页组件
├── pages/               # 页面组件
│   ├── RecordSearch/    # 记录检索页面
│   ├── RecordDetail/    # 记录详情页面
│   └── AnalysisResult/  # 分析结果页面
├── services/            # API 服务
│   ├── recordService.ts
│   └── analysisService.ts
└── types/               # 类型定义
    └── index.ts
```

## 组件说明

### 1. SearchPanel (检索条件面板)
- **功能**: 提供多条件检索功能
- **特性**: 
  - 可折叠/展开
  - 支持关键词、数据库、表名、时间范围等筛选
  - 快速筛选标签
- **Props**:
  - `criteria: SearchCriteria` - 当前检索条件
  - `onSearch: (criteria) => void` - 搜索回调
  - `onReset: () => void` - 重置回调

### 2. RecordTable (记录表格)
- **功能**: 展示慢 SQL 记录列表
- **特性**:
  - 支持多选和批量操作
  - 分页显示
  - 状态和风险等级可视化
  - SQL 预览和详情查看
- **Props**:
  - `records: SlowSqlRecord[]` - 记录列表
  - `total: number` - 总记录数
  - `page: number` - 当前页码
  - `pageSize: number` - 每页数量
  - `onPageChange: (page, pageSize) => void` - 分页回调
  - `onRecordClick: (record) => void` - 记录点击回调
  - `onAnalyze: (ids) => void` - 分析回调
  - `onExport: (ids) => void` - 导出回调

### 3. AnalysisResult (分析结果页面)
- **功能**: 展示分析结果详情
- **特性**:
  - 分析概览信息
  - 根本原因分析
  - 优化建议列表
  - PDF 报告下载
- **Props**:
  - `resultId: string` - 分析结果 ID

## 样式设计

### 颜色方案
```css
/* 状态颜色 */
.status-pending { color: #d9d9d9; }
.status-analyzing { color: #1890ff; }
.status-completed { color: #52c41a; }
.status-failed { color: #ff4d4f; }

/* 风险等级颜色 */
.risk-low { color: #52c41a; }
.risk-medium { color: #faad14; }
.risk-high { color: #ff4d4f; }
.risk-critical { color: #cf1322; }

/* 执行时间颜色 */
.execution-time-green { color: #52c41a; }  /* < 1s */
.execution-time-orange { color: #faad14; } /* 1-3s */
.execution-time-red { color: #ff4d4f; }    /* > 3s */
```

### 布局规范
- 页面最大宽度: 1400px
- 内容区域 padding: 24px
- 组件间距: 16px
- 圆角: 4px
- 阴影: 0 2px 8px rgba(0,0,0,0.1)

## 交互设计

### 加载状态
- 使用骨架屏或加载动画
- 异步操作显示 Toast 提示

### 空状态
- 友好的空状态提示
- 提供操作建议

### 错误处理
- 错误信息以 Toast 形式展示
- 网络错误提供重试按钮

