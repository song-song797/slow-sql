# Slow SQL Backend

后端启动方式和联调步骤已统一收敛到仓库根目录说明：

- `../../README.md`

当前后端默认运行在容器中，由根目录 `docker-compose.local.yml` 统一编排。

后端默认能力：

- 慢 SQL 检索接口
- 分析任务提交、任务列表、报告查询
- PDF 报告代理下载
- `/health` 和 `/ready` 健康检查

默认访问地址：

- `http://127.0.0.1:10800/docs`
