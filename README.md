# Slow SQL 本地联调说明

这个仓库包含两个子项目：

- `slow-sql-backend-main/slow-sql-backend-main`：FastAPI 后端
- `slow-sql-web-main/slow-sql-web-main`：React 前端静态站点

当前默认运行方式已经收敛为完整容器化部署，所有本地端口和服务依赖统一由根目录 `docker-compose.local.yml` 管理。

## 1. 配置远端报告工作流

分析报告能力依赖远端 workflow，请先在仓库根目录准备环境变量。最简单的方式是先在当前 shell 导出：

```bash
export REPORT_PROVIDER=api1_workflow
export REPORT_API_BASE_URL=http://your-host/api/v2/workflow/invoke
export WORKFLOW_ID=your-workflow-id
```

说明：

- `REPORT_API_BASE_URL` 和 `WORKFLOW_ID` 由远端 workflow 提供
- 如果未配置，前后端容器仍可启动，但分析任务会失败

## 2. 启动完整环境

在仓库根目录执行：

```bash
./scripts/run-project
```

这个脚本会统一启动：

- MySQL
- Elasticsearch
- ES 初始化种子任务
- Backend
- Frontend

也可以直接执行：

```bash
docker compose -f docker-compose.local.yml up -d --build
```

默认访问地址：

- 前端：`http://127.0.0.1:3000`
- 后端 Swagger：`http://127.0.0.1:10800/docs`
- 后端健康检查：`http://127.0.0.1:10800/health`
- 后端依赖检查：`http://127.0.0.1:10800/ready`

## 3. 停止和重启

停止：

```bash
./scripts/stop-project
```

重启：

```bash
./scripts/restart-project
```

对应的原生命令：

```bash
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --build
```

## 4. 容器内服务关系

- 前端容器通过 Nginx 反向代理把 `/api/*` 转发到后端容器
- 后端容器通过容器网络访问：
  - MySQL：`mysql:3306`
  - Elasticsearch：`elasticsearch:9200`
- 宿主机默认只暴露：
  - 前端 `3000`
  - 后端 `10800`

## 6. 服务器部署地址

线上服务部署在 `172.20.40.166`，端口说明如下：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://172.20.40.166:3000 | 慢SQL分析系统Web界面 |
| 后端 API 文档 | http://172.20.40.166:10800/docs | Swagger UI |
| Kafka 管理界面 | http://172.20.40.166:9000 | Kafka 消费监控 |
| 日志上传工具 | http://172.20.40.166:8090 | 日志上传管理 |

## 5. 最小联调验证

### 查询慢 SQL

打开首页后应能看到至少一条示例记录：

- 数据库：`slow_sql_db`
- SQL 示例：`SELECT * FROM orders ...`
- 执行时间大于 1 秒

### 提交分析

在记录列表里点击“分析”：

- 会创建一条 `pending` 任务
- 如果远端 workflow 配置正确，任务会继续推进到 `completed` 或 `failed`
- 页面会跳转到分析结果页并按 `task_id` 过滤

### 查看和下载报告

- 报告链接由远端 workflow 返回
- 如果浏览器直连下载失败，后端仍可通过 `/api/v1/sql-analysis/download-pdf` 代理下载
