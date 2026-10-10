# 决策记录

记录关键实现决策及原因，便于后续回溯。

- 使用 LangGraph `StateGraph` 手动构建最小循环，而不是直接使用高层封装，便于面试讲解 Agent Loop 细节。
- Phase 1 的 Tool 直接定义在 `app/agent.py` 内，暂不新建 `tools/`，避免创建无实际用途的文件。
- `.env` 使用显式绝对路径加载，避免受启动目录影响。
- 模型调用使用 `langchain-openai` 的 `ChatOpenAI`，通过 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` 支持 OpenAI 兼容服务；本项目选择 DeepSeek。
- 缺配置返回 HTTP 500（配置错误）、执行异常返回 HTTP 502，均带明确原因，不静默失败。
- 图执行设置 `recursion_limit=10`，防止工具循环失控。
- 明确区分「已实现」与「计划实现」，不虚报尚未完成的功能。
