# Enterprise Data Analyst Agent

基于 **FastAPI + LangGraph** 的电商数据分析 Agent：把「自然语言提问 → 工具调用 → 真实数据查询 → 自然语言回答」串成一条可控、可观测、不编造数据的自动链路。

面向 AI 应用开发 / Agent 开发方向的求职作品集项目，用于证明对 LLM Agent Loop、LangGraph、Tool Calling、NL2SQL、RAG、FastAPI 的工程理解。

## 架构

```
用户 → FastAPI POST /chat
     → LangGraph StateGraph (START → agent → tools → agent → END)
     → ToolNode 执行工具 → 结果回灌 LLM → 最终回答
```

## 已实现能力

| 能力 | 说明 |
| --- | --- |
| Agent Loop | `StateGraph(MessagesState)` + `ToolNode` + `tools_condition` |
| 多轮记忆 | `MemorySaver` 按 `thread_id` 保存会话上下文，`recursion_limit=10` 防失控 |
| NL2SQL | 自然语言 → 只读 SQL，在 438,974 条真实清洗数据上执行 |
| 专用分析 Tool | 销售概况、销售趋势（按月）、品牌 Top10、地区 Top10 |
| RAG | 本地 TF-IDF + 余弦相似度检索口径知识（无需向量数据库） |
| 防幻觉 | 系统提示强制「先调工具、用真实数字作答、禁止编造」 |
| 容错 | 配置缺失返回 500、执行异常返回 502，不静默失败 |

## NL2SQL 的四层安全控制

1. 清洗后数据载入**内存 SQLite**，并开启 `PRAGMA query_only = ON`，数据库层禁止写入；
2. 语法校验：只允许单条 `SELECT` 或 `WITH ... SELECT`，禁止分号拼接；
3. 关键字黑名单：INSERT / UPDATE / DELETE / DROP / ALTER / CREATE / REPLACE / ATTACH / PRAGMA 等全部拦截；
4. 自动追加 `LIMIT 20`（已有 LIMIT 且超限则改写），并用 `threading.Lock` 保证并发安全。

## 技术栈

Python 3.11 · FastAPI · LangGraph 1.x · LangChain 1.x · langchain-openai（OpenAI 兼容协议，可接 DeepSeek）· pandas · numpy · pydantic · python-dotenv · SQLite（内存只读）

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env   # 填写 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL

uvicorn app.main:app --reload
```

请求示例：

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "哪个品牌销售额最高？", "thread_id": "demo"}'
```

## 数据来源

复用**电商用户行为分析项目**清洗后的 43.9 万条数据，通过 `importlib` 动态加载原项目 `data_processor.py` 并只读引用，不修改原项目任何文件。运行前请确认 `app/data_tool.py` 中的 `ORIGINAL_DATA_DIR` 与 `DATA_PROCESSOR_PATH` 指向本地实际路径。

> 原项目与本 Agent 相互独立，数据目录名含中文，CSV 需按 `gb2312` 编码读取。

## 后续规划

RFM / KMeans 分析 Tool · Plotly 图表 Tool · Streamlit 前端 · MCP 接入 · Agent Evaluation 评测集

## 目录结构

```
D:\Agent_project
├─ .env.example          # 配置模板（.env 不入库）
├─ requirements.txt
├─ app
│  ├─ agent.py           # LangGraph 编排 + 系统提示
│  ├─ data_tool.py       # 7 个 Tool + NL2SQL 校验 + TF-IDF RAG
│  ├─ main.py            # FastAPI POST /chat
│  └─ mcp_server.py
└─ docs
   ├─ PROJECT.md  CURRENT_STATUS.md  DEVELOPMENT_LOG.md
   └─ PROBLEMS.md DECISIONS.md       TEST_RECORD.md
```
