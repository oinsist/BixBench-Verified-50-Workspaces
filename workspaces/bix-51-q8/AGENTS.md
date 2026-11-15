# 工作区约定

阅读 TASK.md 并根据原始英文题目完成分析。

- 在当前工作区内开展分析，输入数据位于 data/，保持原始输入不变。
- 将代码保存在 analysis/，将结果、图表及日志保存在 outputs/。
- 分析说明写入 outputs/report.md，记录数据选择、方法、参数、依赖版本和限制。
- 最终写入 outputs/answer.json，例如 {"answer": "简洁答案", "status": "completed"}。无法完成时用 status="blocked" 并增加 reason 字段。
- 根据实际数据计算，不编造数据或结果，不查找标准答案或参考解题 Notebook。
- 先检查当前环境中的依赖；需要额外工具时记录安装方法和实际版本。
- API 密钥通过运行环境提供，不写入文件或分析输出。
- 文件夹是分析任务入口；Agent 的模型、工具权限和轮数由运行该 Agent 的应用配置。
