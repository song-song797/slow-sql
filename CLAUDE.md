# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 项目特定说明

这个慢SQL分析项目主要用于：
- 监控和分析生产环境中的慢SQL查询
- 通过聚类分析识别高频性能问题
- 生成详细的优化建议报告
- 支持MySQL和PostgreSQL数据库

## 🔧 开发者偏好

- 使用中文进行代码注释和文档说明
- 所有新的API端点需要添加完整的类型注解
- 前端组件优先使用函数式组件和Hooks
- 数据库变更需要通过迁移脚本管理

## 项目概述

这是一个慢SQL分析系统，用于监控、分析和优化数据库SQL性能。系统采用前后端分离架构，通过Elasticsearch存储和检索SQL执行记录，支持MySQL和PostgreSQL数据库。

### 技术栈
- **后端**: FastAPI + Python + SQLAlchemy
- **前端**: React + TypeScript + Vite + Ant Design
- **存储**: MySQL (业务数据) + Elasticsearch (SQL执行记录)
- **报告**: 远端工作流API生成PDF分析报告

## 开发环境启动

### 1. 启动依赖服务
```bash
# 在仓库根目录执行
docker compose -f docker-compose.local.yml up -d --build
```
依赖服务端口：
- MySQL: `127.0.0.1:3306` (用户: slow_sql/slow_sql)
- Elasticsearch: `127.0.0.1:9200` (无需认证)
- Report Stub: `127.0.0.1:18080` (本地模拟报告生成服务)

### 2. 启动后端
```bash
cd slow-sql-backend-main/slow-sql-backend-main
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 10800 --reload
```
后端端口：`10800`
API文档：`http://127.0.0.1:10800/docs`

### 3. 启动前端
```bash
cd slow-sql-web-main/slow-sql-web-main
npm install
npm run dev
```
前端端口：`3000`
访问地址：`http://127.0.0.1:3000`

### 4. 运行测试
```bash
# 后端测试
cd slow-sql-backend-main/slow-sql-backend-main
pytest

# 前端类型检查
cd slow-sql-web-main/slow-sql-web-main
npm run type-check

# 前端lint
npm run lint
```

### 5. 构建前端
```bash
cd slow-sql-web-main/slow-sql-web-main
npm run build
```

## 核心架构

### 后端架构 (FastAPI)
```
app/
├── main.py                 # FastAPI应用入口，路由注册
├── config.py              # 配置管理，支持.env文件覆盖
├── database.py            # 数据库连接和会话管理
├── dependencies.py        # FastAPI依赖注入
├── models/               # SQLAlchemy数据模型
│   ├── analysis_task.py  # 分析任务模型
│   ├── database_info.py  # 数据库信息模型
│   └── data_source.py    # 数据源配置模型
├── routers/              # API路由处理器
│   ├── es_query.py       # ES查询接口
│   ├── sql_analysis.py   # SQL分析任务接口
│   ├── data_sources.py   # 数据源管理接口
│   └── database_info.py  # 数据库信息接口
├── services/             # 业务逻辑服务层
│   ├── es_service.py     # ES查询服务
│   ├── report_service.py # 报告生成和管理
│   ├── analysis_context_service.py # 分析上下文构建
│   └── data_source_service.py # 数据源管理
└── schemas/              # Pydantic数据验证模型
```

### 前端架构 (React)
```
src/
├── App.tsx              # 路由配置，主布局
├── pages/              # 页面组件
│   ├── RecordSearch/          # SQL记录检索页面
│   ├── AnalysisResultList/    # 分析结果列表页面
│   ├── AnalysisReportDetail/  # 报告详情页面
│   └── DataSourceManagement/  # 数据源管理页面
├── components/         # 可复用组件
│   ├── SearchPanel/          # 搜索面板
│   ├── RecordTable/          # 记录表格
│   └── AnalysisSearchPanel/  # 分析搜索面板
└── services/          # API服务封装
    └── api.ts        # 统一的API调用接口
```

## 核心业务流程

### 1. SQL聚类检索流程
- 用户在前端设置检索条件（耗时范围、时间范围、关键词等）
- 调用 `GET /api/v1/es-query/clusters` 进行聚类查询
- Elasticsearch按SQL模板聚合执行记录
- 返回聚类统计信息（执行次数、耗时统计、样本SQL）

### 2. 分析任务提交流程
- 用户选择聚类记录进行分析
- 系统自动匹配数据源（根据db_type、host、port、db_name）
- 调用 `POST /api/v1/sql-analysis/submit` 提交分析任务
- 后端构建分析上下文（元数据、表结构、索引信息）
- 调用远端工作流API生成报告
- 返回task_id供前端轮询

### 3. 数据源管理
- 用户配置数据库连接信息（加密存储）
- 系统测试连接可用性
- 分析时自动匹配数据源获取元数据
- 支持MySQL和PostgreSQL

### 4. 异步任务处理
- 前端每10秒轮询一次任务状态
- 后端查询MySQL中的任务状态
- 完成后提供PDF报告下载

## 关键配置说明

### 后端配置 (app/config.py)
主要配置项：
- `api_key`: API密钥 (默认: dev-api-key)
- `es_url`: Elasticsearch地址
- `report_provider`: 报告生成方式 (api1_workflow/local_stub)
- `metadata_auto_fetch_enabled`: 是否自动获取元数据
- `metadata_db_overrides`: 元数据获取覆盖配置

### 前端配置
主要环境变量：
- `VITE_API_BASE_URL`: 后端API地址
- `VITE_API_KEY`: API密钥

## 数据库Schema

### analysis_task 表
分析任务核心表，存储：
- 任务状态 (pending/completed/failed)
- 报告URL
- SQL文本和分析上下文
- 风险等级 (1-低风险, 2-中风险, 3-高风险)
- 数据源关联信息

### database_info 表
存储数据库元数据信息：
- 数据库类型、名称、版本
- 表名、表结构DDL
- 表行数统计

### data_source 表
数据源配置表：
- 数据库连接信息（加密存储）
- 启用状态和测试状态
- 创建和更新时间

## 重要设计原则

### 1. 渐进式兼容
- 当无数据源匹配时，以兼容模式运行分析
- 在报告中明确标注元数据缺失情况
- 保证基本功能可用性

### 2. 异步处理
- 分析任务采用异步处理模式
- 前端轮询获取进度，避免长时间等待
- 后端在数据库中维护任务状态

### 3. 智能聚类
- 相同SQL模板的执行记录聚合成类
- 便于识别高频慢SQL问题
- 支持按多个维度排序和筛选

### 4. 元数据增强
- 自动从数据源获取表结构、索引信息
- 支持多数据库类型（MySQL、PostgreSQL）
- 可配置元数据获取策略

## API端点概览

### ES查询相关
- `GET /api/v1/es-query` - 基础SQL记录查询
- `GET /api/v1/es-query/clusters` - 按SQL模板聚类查询

### 分析任务相关
- `POST /api/v1/sql-analysis/submit` - 提交SQL分析任务
- `GET /api/v1/sql-analysis/tasks` - 获取分析任务列表
- `GET /api/v1/sql-analysis/tasks/{task_id}` - 获取任务详情
- `GET /api/v1/sql-analysis/report/{task_id}` - 获取报告URL
- `POST /api/v1/sql-analysis/download-pdf` - 代理下载PDF报告
- `POST /api/v1/sql-analysis/download-pdfs` - 批量下载PDF报告
- `POST /api/v1/sql-analysis/tasks/{task_id}/hide` - 隐藏任务

### 数据源相关
- `GET /api/v1/data-sources` - 获取数据源列表
- `POST /api/v1/data-sources` - 创建数据源
- `PUT /api/v1/data-sources/{id}` - 更新数据源
- `DELETE /api/v1/data-sources/{id}` - 删除数据源
- `POST /api/v1/data-sources/{id}/test` - 测试数据源连接

### 健康检查
- `GET /health` - 基础健康检查
- `GET /ready` - 依赖服务就绪检查（数据库、ES、报告服务）

## 开发注意事项

### 后端开发
- 使用SQLAlchemy ORM进行数据库操作
- 通过`get_db()`依赖注入获取数据库会话
- 所有API端点都需要API Key验证（`verify_api_key`）
- 使用Pydantic进行请求/响应数据验证
- 遵循FastAPI依赖注入模式

### 前端开发
- 使用TypeScript严格模式
- 组件采用函数式组件 + Hooks
- 使用Ant Design组件库
- API调用统一通过`services/api.ts`
- 路由使用React Router v6

### 数据库迁移
- 数据库表结构通过`init_database()`自动创建
- 支持增量添加字段的迁移机制
- 使用`_ensure_*_columns()`函数确保字段存在
- MySQL使用LONGTEXT存储大文本

### 测试
- 后端使用pytest进行测试
- 测试文件位于`tests/`目录
- 前端无专门的测试配置
- 使用`/ready`端点验证依赖服务状态