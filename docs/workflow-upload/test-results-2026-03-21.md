# 2026-03-21 文件上传格式回归结果

## 结论

截至 2026-03-21，这轮“只改上传文件格式、不改工作流”的实测结果是：

1. `V1 -> V2 -> V3` 可以修复“工作流把文件判成 0 条 SQL”的问题
2. `V3` 相比旧样例，已经能更稳定回显表名、主键和部分索引名
3. 但仍然无法稳定修复以下关键问题：
   - `table_rows_exact / table_rows` 仍被工作流改写成 `0`
   - 已提供的 DDL / 索引仍会被工作流写成“为空 / 未提供 / 无索引”
   - 部分字段仍会被按命名习惯错误推断成主键

因此，当前可以明确得出结论：

仅靠上传文件格式，无法彻底解决这个 workflow 的元数据识别问题。  
如果要把问题真正关掉，下一步必须进入 workflow 侧，调整其中间抽取节点或总结提示词，或者增加结果校验。

## 已执行的真实回归

### 1. 控制组

- 上传文件：[manual-workflow-input.sample.md](/D:/software_test/slow-sql/docs/manual-workflow-input.sample.md)
- 工作流报告：[control.manual-sample.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/control.manual-sample.report.md)
- 校验结果：失败，仍存在“无索引 / 行数失真 / 主键乱猜”

结论：
- 旧格式能让工作流识别出 `10` 条 SQL
- 但不能保证它正确消费 DDL、索引和行数

### 2. Baseline Case A

- V1 首轮报告：[case-a.v1.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/case-a.v1.report.md)
  - 问题：工作流把文件识别成 `0` 条 SQL
- V1 调整骨架后二轮报告：[case-a.v1.round2.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/case-a.v1.round2.report.md)
  - 改善：能识别 `customer`、主键 `id`、索引名
  - 未解决：仍把行数写成 `0`，仍把 `cust_id` 往主键上靠
- V2 报告：[case-a.v2.round2.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/case-a.v2.round2.report.md)
  - 结果：比 V1 没有本质改善
- V3 报告：[case-a.v3.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/case-a.v3.report.md)
  - 改善：不再出现“DDL 为空 / 无索引”这类全局失败词
  - 未解决：`table_rows=0` 仍然存在，`cust_id` 仍被错误推断为主键候选

### 3. Baseline Case C

- V3 报告：[case-c.v3.report.md](/D:/software_test/slow-sql/docs/workflow-upload/reports/case-c.v3.report.md)
- 校验结果：失败

未解决的问题：
- 仍未正确回显 `8600000`
- 仍把已提供的 DDL / 索引写成缺失或不确定

## 当前最有价值的保留产物

- 上传文件模板说明：[README.md](/D:/software_test/slow-sql/docs/workflow-upload/README.md)
- 验收清单：[checklist.md](/D:/software_test/slow-sql/docs/workflow-upload/checklist.md)
- 生成脚本：[generate_workflow_upload_artifacts.py](/D:/software_test/slow-sql/scripts/generate_workflow_upload_artifacts.py)
- 校验脚本：[validate_workflow_report.py](/D:/software_test/slow-sql/scripts/validate_workflow_report.py)
- 真实工作流回归脚本：[run_workflow_file_regression.py](/D:/software_test/slow-sql/scripts/run_workflow_file_regression.py)

## 推荐后续动作

1. 对外给 workflow 同学时，优先带上 `case-a.v3` 和 `case-c.v3` 的输入、输出和校验结果
2. 重点要求他们检查：
   - 抽取节点是否把 `table_rows_exact` 缺省成 `0`
   - 总结节点是否忽略了 `AUTHORIZED_METADATA_JSON / LOCAL_FACT_PACKET_JSON`
   - 文件节点传入的 DDL 与索引信息是否在中间结构化结果里丢失
3. 如果 workflow 侧暂时不能改，业务上建议继续使用旧格式或 `V3` 作为相对更稳的输入，但不要把它当成“问题已经根治”
