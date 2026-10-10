# 开发日志

按时间倒序记录。

## 2026-09-21

- Phase 2（第一工具）：新增 `app/data_tool.py`，复用原项目 DataProcessor 实现真实数据 Tool `get_sales_overview`；接入 Agent，真实 LLM 与 `/chat` 均返回真实数字。
- 建立开发归档系统：在 `docs/` 下创建 7 个 Markdown 文件。
- Phase 1 验证通过：真实 `/chat` 请求返回 HTTP 200（DeepSeek）。
- Phase 1 实现：LangGraph 最小 Agent Loop + FastAPI `/chat` + 单个确定性 Tool。
- 初始化：确认项目目录、检查已安装依赖版本、核对 LangGraph 1.x / LangChain 1.x API 签名。
