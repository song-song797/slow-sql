# 工作流文件上传格式回归

这套目录只解决一件事：在不改工作流节点和提示词的前提下，通过改上传文件格式，提高工作流对 `DDL / 表结构 / 索引` 的识别稳定性。

## 目录说明

- `baseline/`：3 个基线 Case 的 `v1 / v2 / v3` 上传文件和 manifest
- `batch/`：10 条 SQL 的批量上传文件，以及 V3 的拆分组文件
- `reports/`：真实工作流回归输出目录
- `checklist.md`：人工验收清单

## 推荐顺序

1. 先跑 `baseline/case-a.v1.md`
2. 若失败，再跑同 case 的 `v2`
3. 若仍失败，再跑同 case 的 `v3`
4. `case-a / case-b / case-c` 都通过后，再跑 `batch/all-10.v2.md`
5. 若 10 条混装退化，再跑 `batch/group-*.v3.md`

## 生成上传文件

```powershell
D:\software_test\slow-sql\slow-sql-backend-main\slow-sql-backend-main\.venv\Scripts\python.exe `
  D:\software_test\slow-sql\scripts\generate_workflow_upload_artifacts.py
```

## 校验已有报告

```powershell
D:\software_test\slow-sql\slow-sql-backend-main\slow-sql-backend-main\.venv\Scripts\python.exe `
  D:\software_test\slow-sql\scripts\validate_workflow_report.py `
  --manifest D:\software_test\slow-sql\docs\workflow-upload\baseline\case-a.v2.manifest.json `
  --report D:\software_test\slow-sql\docs\workflow-upload\reports\case-a.v2.report.md `
  --output-json D:\software_test\slow-sql\docs\workflow-upload\reports\case-a.v2.validation.json `
  --output-md D:\software_test\slow-sql\docs\workflow-upload\reports\case-a.v2.validation.md
```

## 直接跑真实工作流回归

```powershell
D:\software_test\slow-sql\slow-sql-backend-main\slow-sql-backend-main\.venv\Scripts\python.exe `
  D:\software_test\slow-sql\scripts\run_workflow_file_regression.py `
  --upload D:\software_test\slow-sql\docs\workflow-upload\baseline\case-a.v2.md `
  --manifest D:\software_test\slow-sql\docs\workflow-upload\baseline\case-a.v2.manifest.json `
  --label case-a.v2
```
