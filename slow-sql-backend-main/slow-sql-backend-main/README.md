# Slow SQL Backend

后端本地运行方式和联调步骤已统一收敛到仓库根目录说明：

- `../../README.md`

后端默认能力：

- 慢 SQL 检索接口
- 分析任务提交、任务列表、报告查询
- PDF 报告代理下载
- `/health` 和 `/ready` 健康检查

默认本地运行命令：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 10800 --reload
```
