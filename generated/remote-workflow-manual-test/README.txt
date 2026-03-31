这三个事实已经确认：

1. 当前远端 workflow 的输入事件字段名是 sql_text，不是 document2。
2. 当前远端 workflow 的输入节点 node_id 是运行时返回的，今天抓到的一次示例值为 input_74b6d。
3. 后端最终提交给远端的是一份 Markdown 文档，原文见同目录下的 .md 文件。

手工测试建议：

1. 先请求一次：
   POST http://172.20.20.128:3001/api/v2/workflow/invoke
   body:
   {
     "workflow_id": "fb594dae47c5440dbea05725ebec6674",
     "stream": false
   }

2. 在返回事件里找到：
   - input 事件
   - node_id
   - input_schema.value[0].key

3. 再把 markdown 文件内容填到那个 key 里重新提交。

4. 如果你在平台页面手工测，不需要关心外层 JSON，只需要把 markdown 原文填进 sql_text 输入框。

注意：
- request-shape-example.json 里的 input_74b6d 是今天抓到的一次示例，不保证每次都一样。
- markdown 里 column_definitions 的 salary_total 被截成了 decimal(12，这是后端本地列摘要解析的小 bug，但不影响 DDL 正文已经被带上。
