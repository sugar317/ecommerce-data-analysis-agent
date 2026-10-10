# 基于 LangGraph 的电商数据分析 Agent

用 LangGraph 搭建的电商数据分析智能体：自然语言提问 → 意图识别 → 工具调用（NL2SQL / 统计聚合 / RAG 检索）→ 结果解释，支持多轮对话与结构化表格输出。

## 能力

- **意图路由**：把用户问题分派到不同 Tool（销售概况、品牌排行、NL2SQL 明细查询、指标解释）
- **NL2SQL 安全控制**：只允许只读查询、限制返回行数、校验表名与字段白名单
- **RAG 检索**：对指标口径 / 业务文档做向量检索后注入上下文
- **接口封装**：FastAPI 提供 `/chat` 接口，附带一个演示用聊天页面 `demo_chat.html`

## 目录

```
app/             # Agent 主程序（图定义、Tool、检索、API）
docs/            # 设计说明与问题复盘
requirements.txt
demo_chat.html   # 本地演示聊天页
```

## 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入模型 API Key
uvicorn app.main:app --host 0.0.0.0 --port 8000
# 浏览器打开 demo_chat.html 即可对话
```

## 技术栈

Python · LangGraph · FastAPI · SQLite/CSV 数据源 · 向量检索
